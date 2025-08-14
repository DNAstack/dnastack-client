import os
import uuid
from typing import Optional, Iterable, List

import click
from click import style, Group

from dnastack.cli.commands.workbench.runs.utils import UnableToFindParameterError, NoDefaultEngineError
from dnastack.cli.commands.utils import MAX_RESULTS_ARG, PAGINATION_PAGE_ARG, PAGINATION_PAGE_SIZE_ARG
from dnastack.cli.commands.workbench.utils import get_ewes_client, NAMESPACE_ARG, create_sort_arg, \
    parse_to_datetime_iso_format
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import ArgumentSpec, ArgumentType, CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG
from dnastack.cli.helpers.exporter import to_json, normalize
from dnastack.cli.helpers.iterator_printer import show_iterator, OutputFormat
from dnastack.client.workbench.ewes.models import ExtendedRunListOptions, ExtendedRunRequest, \
    BatchRunRequest, \
    MinimalExtendedRunWithOutputs, MinimalExtendedRunWithInputs, ExecutionEngineListOptions, SimpleSample
from dnastack.client.workbench.common.models import State
from dnastack.client.workbench.ewes.models import LogType
from dnastack.common.json_argument_parser import JsonLike, parse_and_merge_arguments, merge, merge_param_json_data
from dnastack.common.tracing import Span


def init_runs_commands(group: Group):
    @formatted_command(
        group=group,
        name='list',
        specs=[
            MAX_RESULTS_ARG,
            PAGINATION_PAGE_ARG,
            PAGINATION_PAGE_SIZE_ARG,
            create_sort_arg('--sort "end_time:ASC", --sort "workflow_id;end_time:DESC;"'),
            ArgumentSpec(
                name='order',
                arg_names=['--order'],
                help='This flag is now deprecated, please use --sort instead. Define the ordering of the results. '
                     'The value should return to the attribute name to order the results by. '
                     'By default, results are returned in descending order. '
                     'To change the direction of ordering include the "ASC" or "DESC" string after the column. '
                     'e.g.: --O "end_time", --O "end_time ASC"',
            ),
            ArgumentSpec(
                name='states',
                arg_names=['--state'],
                help='Filter the results by their state. This flag can be defined multiple times, with the result being runs matching any of the states.',
                type=State,
                choices=[e.value for e in State],
                multiple=True,
            ),
            ArgumentSpec(
                name='submitted_since',
                arg_names=['--submitted-since'],
                help='Filter the results with their start_time greater or equal to the since timestamp. '
                     'The timestamp can be in iso date, or datetime format. '
                     'e.g.: -f "2022-11-23", -f "2022-11-23T00:00:00.000Z"',
            ),
            ArgumentSpec(
                name='submitted_until',
                arg_names=['--submitted-until'],
                help='Filter the results with their start_time strictly less than the since timestamp. '
                     'The timestamp can be in iso date, or datetime format. '
                     'e.g.: -t "2022-11-23", -t "2022-11-23T23:59:59.999Z"',
            ),
            ArgumentSpec(
                name='engine',
                arg_names=['--engine'],
                help='Filter the results to runs with the given engine ID.',
            ),
            ArgumentSpec(
                name='search',
                arg_names=['--search'],
                help='Perform a full text search across various fields using the search value.',
            ),
            ArgumentSpec(
                name='tags',
                arg_names=['--tags'],
                help='Filter runs by one or more tags. Tags can be specified as a KV pair, inlined JSON, or as a json file preceded by the "@" symbol.',
                type=JsonLike,
            ),
            ArgumentSpec(
                name='samples',
                arg_names=['--sample'],
                help='Filter runs by one or more sample IDs. Can be specified multiple times',
                multiple=True,
            ),
            ArgumentSpec(
                name='storage_account_id',
                arg_names=['--storage-account'],
                help='Filter runs by the storage account ID. This will return runs that have outputs stored in the specified storage account.',
            ),
            NAMESPACE_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def list_runs(context: Optional[str],
                  endpoint_id: Optional[str],
                  namespace: Optional[str],
                  max_results: Optional[int],
                  page: Optional[int],
                  page_size: Optional[int],
                  sort: Optional[str],
                  order: Optional[str],
                  submitted_since: Optional[str],
                  submitted_until: Optional[str],
                  engine: Optional[str],
                  search: Optional[str],
                  tags: JsonLike,
                  samples: Optional[List[str]] = None,
                  storage_account_id: Optional[str] = None,
                  states: Optional[List[State]] = None):
        """
        List workflow runs

        docs: https://docs.omics.ai/products/command-line-interface/reference/workbench/runs-list
        """

        order_direction = None
        if order:
            order_and_direction = order.split()
            if len(order_and_direction) > 1:
                order = order_and_direction[0]
                order_direction = order_and_direction[1]

        if tags:
            tags = tags.parsed_value()
            tags = [f"{k}:{v}" for k, v in tags.items()]

        client = get_ewes_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
        list_options: ExtendedRunListOptions = ExtendedRunListOptions(
            page=page,
            page_size=page_size,
            sort=sort,
            order=order,
            direction=order_direction,
            state=states,
            since=parse_to_datetime_iso_format(date=submitted_since, start_of_day=True),
            until=parse_to_datetime_iso_format(date=submitted_until, end_of_day=True),
            engine_id=engine,
            search=search,
            sample_ids=samples,
            storage_account_id=storage_account_id,
            tag=tags
        )
        runs_list = client.list_runs(list_options, max_results)
        show_iterator(output_format=OutputFormat.JSON, iterator=runs_list)

    @formatted_command(
        group=group,
        name='describe',
        specs=[
            ArgumentSpec(
                name='run_id',
                arg_type=ArgumentType.POSITIONAL,
                help='Specify one or more run ID\'s that you would like to retrieve information for.',
                required=True,
                multiple=True
            ),
            NAMESPACE_ARG,
            ArgumentSpec(
                name='status',
                arg_names=['--status'],
                help='Output a minimal response, only showing the status id, current state, start and stop times.',
                type=bool,
            ),
            ArgumentSpec(
                name='inputs',
                arg_names=['--inputs'],
                help='Display only the run\'s inputs as json.',
                type=bool,
            ),
            ArgumentSpec(
                name='outputs',
                arg_names=['--outputs'],
                help='Display only the run\'s outputs as json.',
                type=bool,
            ),
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def describe_runs(context: Optional[str],
                      endpoint_id: Optional[str],
                      namespace: Optional[str],
                      run_id: List[str],
                      status: Optional[bool],
                      inputs: Optional[bool],
                      outputs: Optional[bool]):
        """
        Describe one or more workflow runs

        docs: https://docs.omics.ai/docs/runs-describe
        """
        client = get_ewes_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)

        if not run_id:
            click.echo(style("You must specify at least one run ID", fg='red'), err=True, color=True)
            exit(1)

        if status:
            described_runs = [client.get_status(run_id=run) for run in run_id]
        else:
            described_runs = [client.get_run(run_id=run) for run in run_id]

            if inputs:
                described_runs = [MinimalExtendedRunWithInputs(
                    run_id=described_run.run_id,
                    inputs=described_run.request.workflow_params,
                ) for described_run in described_runs]
            elif outputs:
                described_runs = [MinimalExtendedRunWithOutputs(
                    run_id=described_run.run_id,
                    outputs=described_run.outputs
                ) for described_run in described_runs]
        click.echo(to_json(normalize(described_runs)))

    @formatted_command(
        group=group,
        name='cancel',
        specs=[
            ArgumentSpec(
                name='run_id',
                arg_type=ArgumentType.POSITIONAL,
                help='Specify one or more run ID\'s that you would like to cancel.',
                required=True,
                multiple=True
            ),
            NAMESPACE_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def cancel_runs(context: Optional[str],
                    endpoint_id: Optional[str],
                    namespace: Optional[str],
                    run_id: List[str] = None):
        """
        Cancel one or more workflow runs

        docs: https://docs.omics.ai/docs/runs-cancel
        """
        client = get_ewes_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
        if not run_id:
            click.echo(style("You must specify at least one run ID", fg='red'), err=True, color=True)
            exit(1)
        result = client.cancel_runs(run_id)
        click.echo(to_json(normalize(result)))

    @formatted_command(
        group=group,
        name='delete',
        specs=[
            ArgumentSpec(
                name='run_id',
                arg_type=ArgumentType.POSITIONAL,
                help='Specify one or more run ID\'s that you would like to delete.',
                required=True,
                multiple=True
            ),
            ArgumentSpec(
                name='force',
                arg_names=['--force', '-f'],
                help='Force the deletion without prompting for confirmation.',
                type=bool,
            ),
            NAMESPACE_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def delete_runs(context: Optional[str],
                    endpoint_id: Optional[str],
                    namespace: Optional[str],
                    force: Optional[bool] = False,
                    run_id: List[str] = None):
        """
        Delete one or more workflow runs

        docs: https://docs.omics.ai/docs/runs-delete
        """
        client = get_ewes_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
        if not run_id:
            click.echo(style("You must specify at least one run ID", fg='red'), err=True, color=True)
            exit(1)

        if not force and not click.confirm('Do you want to proceed?'):
            return
        result = client.delete_runs(run_id)
        click.echo(to_json(normalize(result)))

    @formatted_command(
        group=group,
        name='logs',
        specs=[
            ArgumentSpec(
                name='run_id_or_log_url',
                arg_type=ArgumentType.POSITIONAL,
                help='Specify a run ID or log URL to retrieve logs.',
                required=True,
                multiple=False
            ),
            NAMESPACE_ARG,
            ArgumentSpec(
                name='log_type',
                arg_names=['--log-type'],
                help='Print only stderr or stdout to the current console.',
                type=LogType,
                choices=[e.value for e in LogType],
                default=LogType.STDOUT.value
            ),
            ArgumentSpec(
                name='task_id',
                arg_names=['--task-id'],
                help='Retrieve logs associated with the given task in the run.',
            ),
            ArgumentSpec(
                name='max_bytes',
                arg_names=['--max-bytes'],
                help='Limit number of bytes to retrieve from the log stream.',
                type=int
            ),
            ArgumentSpec(
                name='output',
                arg_names=['--output'],
                help="Save the output to the defined path, if it does not exist.",
            ),
            ArgumentSpec(
                name='offset',
                arg_names=['--offset'],
                help="Save the output to the defined path, if it does not exist.",
                type=int
            ),
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def get_run_logs(context: Optional[str],
                     endpoint_id: Optional[str],
                     namespace: Optional[str],
                     run_id_or_log_url: str,
                     output: Optional[str],
                     log_type: Optional[LogType] = LogType.STDOUT,
                     task_id: Optional[str] = None,
                     max_bytes: Optional[int] = None,
                     offset: Optional[int] = None):
        """
        Get logs of a single workflow run or task

        docs https://docs.omics.ai/docs/runs-logs
        """
        span = Span()

        def get_writer(output_path: Optional[str]):
            if not output_path:
                return click.echo
            if os.path.exists(output_path):
                click.echo(style(f"{output_path} already exists, command will not overwrite", fg="red"), color=True)
                exit(0)

            output_file = open(output_path, "w")

            def write(binary_content: bytes):
                output_file.write(binary_content.decode("utf-8"))

            return write

        def is_valid_uuid(val: str):
            try:
                uuid.UUID(val, version=4)
                return True
            except ValueError:
                return False

        def print_logs_by_url(log_url: str, writer):
            write_logs(client.stream_log_url(log_url=log_url, max_bytes=max_bytes, offset=offset, trace=span), writer)

        def write_logs(iterable: Iterable[bytes], writer):
            for chunk in iterable:
                if chunk:
                    writer(chunk)

        client = get_ewes_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
        output_writer = get_writer(output)

        if not is_valid_uuid(run_id_or_log_url):
            print_logs_by_url(log_url=run_id_or_log_url, writer=output_writer)
            return

        if task_id:
            write_logs(
                client.stream_task_logs(run_id_or_log_url, task_id, log_type, max_bytes=max_bytes, offset=offset),
                output_writer)
        else:
            write_logs(client.stream_run_logs(run_id_or_log_url, log_type, max_bytes=max_bytes, offset=offset),
                       output_writer)

    @formatted_command(
        group=group,
        name='submit',
        specs=[
            ArgumentSpec(
                name='input_overrides',
                arg_type=ArgumentType.POSITIONAL,
                help='Positional JSON Data that will take precedence over default-params and workflow-params. '
                     'If a value specified in the override collides with a value in the default-params or workflow-params, '
                     'they will be overridden with the value provided in the override. '
                     'If a key with the same name is already provided in the default-params or workflow-params, '
                     'they will be overridden with the value provided in the override.',
                required=False,
                multiple=True
            ),
            ArgumentSpec(
                name='workflow_url',
                arg_names=['--url'],
                help='The URL to the workflow file (*.wdl). The url should contain the workflow id followed by the version. '
                     'See https://docs.omics.ai/products/workbench/workflows/discovering-workflows#navigating-the-workflows-table on how to find the workflow id.',
                required=False,
            ),
            ArgumentSpec(
                name='workflow',
                arg_names=['--workflow'],
                help='The id of the workflow to run. '
                     'See https://docs.omics.ai/products/workbench/workflows/discovering-workflows#navigating-the-workflows-table on how to find the workflow id.',
                required=False,
            ),
            ArgumentSpec(
                name='version',
                arg_names=['--version'],
                help='The version of the workflow to run.',
                required=False,
            ),
            ArgumentSpec(
                name='engine_id',
                arg_names=['--engine'],
                help='Use the given engine id for execution of runs. If this value is not defined then it is assumed '
                     'that the default engine will be used.',
            ),
            ArgumentSpec(
                name='default_workflow_engine_parameters',
                arg_names=['--engine-params'],
                help='Set the global engine parameters for all runs that are to be submitted. '
                     'Engine params can be specified as inlined JSON, json file preceded by the "@" symbol, '
                     'KV pair, parameter preset ID, or as a comma-separated-list containing any of those types '
                     '(e.g. my-preset-id,key=value,\'{"literal":"json"}\',@file.json).',
                type=JsonLike,
            ),
            ArgumentSpec(
                name='default_workflow_params',
                arg_names=['--default-params'],
                help='Specify the global default inputs as a json file or as inlined json to use when submitting '
                     'multiple runs. Default inputs have the lowest level of precedence and will be overridden '
                     'by any run input or override.',
                type=JsonLike,
            ),
            ArgumentSpec(
                name='workflow_params',
                arg_names=['--workflow-params'],
                help='Optional flag to specify the workflow params for a given run. The workflow params can be any'
                     'JSON-like value, such as inline JSON, command separated key value pairs or a json file referenced'
                     'preceded by the "@" symbol. This field may be repeated, with each repetition specifying '
                     'a separate run request that will be submitted.',
                type=JsonLike,
                multiple=True
            ),
            ArgumentSpec(
                name='tags',
                help='Set the global tags for all runs that are to be submitted. '
                     'Tags can be any JSON-like value, such as inline JSON, command separated key value pairs or'
                     'a json file referenced preceded by the "@" symbol.',
                type=JsonLike,
            ),
            ArgumentSpec(
                name='dry_run',
                arg_names=['--dry-run'],
                help='If specified, the command will print the request without actually submitting the workflow.',
                type=bool,
            ),
            ArgumentSpec(
                name='run_requests',
                arg_names=['--run-request'],
                help='Optional way to specify a complete run request for one or more runs. ',
                type=JsonLike,
                multiple=True
            ),
            ArgumentSpec(
                name="samples",
                arg_names=['--sample'],
                help='An optional flag that accepts a Sample IDs to use in the given workflow. '
                     'If not specified, the workflow will be submitted without any samples. '
                     'Can be specified multiple times',
                multiple=True
            ),
            ArgumentSpec(
                name='sample_ids',
                arg_names=['--samples'],
                help='An optional flag that accepts a comma separated list of Sample IDs to use in the given workflow. '
                     'This flag is deprecated, use --sample instead. '
            ),
            ArgumentSpec(
                name='storage_account_id',
                arg_names=['--storage-account'],
                help='The storage account ID to restrict sample files to when submitting the workflow. ',
            ),
            NAMESPACE_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def submit_batch(context: Optional[str],
                     endpoint_id: Optional[str],
                     namespace: Optional[str],
                     workflow_url: Optional[str],
                     workflow: Optional[str],
                     version: Optional[str],
                     engine_id: Optional[str],
                     default_workflow_engine_parameters: JsonLike,
                     default_workflow_params: JsonLike,
                     tags: JsonLike,
                     workflow_params: JsonLike,
                     input_overrides,
                     dry_run: bool,
                     run_requests: JsonLike,
                     sample_ids: Optional[str], # deprecated, use --samples instead
                     samples: Optional[List[str]] = None,
                     storage_account_id: Optional[str] = None):
        """
        Submit one or more workflows for execution

        docs: https://docs.omics.ai/docs/runs-submit
        """

        # Validation check for mutually exclusive arguments
        if workflow_url and workflow:
            click.echo(style("Error: You cannot specify both --url and --workflow.", fg='red'), err=True, color=True)
            exit(1)

        # Validation check for required arguments
        if not workflow_url and not workflow:
            click.echo(style("Error: You must specify either --url or --workflow.", fg='red'), err=True, color=True)
            exit(1)

        # Validation check for --version without --workflow
        if version and not workflow:
            click.echo(style("Error: You must specify --workflow when using --version.", fg='red'), err=True,
                       color=True)
            exit(1)

        # Validation check for --workflow without --version
        if workflow and not version:
            click.echo(style("Error: You must specify --version when using --workflow.", fg='red'), err=True,
                       color=True)
            exit(1)

        # Combine workflow and version if both are provided
        if workflow and version:
            workflow_url = f"{workflow}/{version}"

        ewes_client = get_ewes_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)

        def parse_samples():
            if samples:
                sample_list = samples
            elif sample_ids:
                sample_list = sample_ids.split(',')
            else:
                return None

            return [SimpleSample(id=sample_id, storage_account_id=storage_account_id) for sample_id in sample_list]

        def get_default_engine_id():
            list_options = ExecutionEngineListOptions()
            engines = ewes_client.list_engines(list_options)
            for engine in engines:
                if engine.default:
                    return engine.id
            raise NoDefaultEngineError("No default engine found. Please specify an engine id using the --engine flag "
                                       "or in the workflow engine parameters list using ENGINE_ID_KEY=....")

        if not engine_id:
            engine_id = get_default_engine_id()

        if default_workflow_engine_parameters:
            [param_ids_list, kv_pairs_list, json_literals_list,
             files_list] = default_workflow_engine_parameters.extract_arguments_list()

            param_presets = merge_param_json_data(kv_pairs_list, json_literals_list, files_list)

            if param_ids_list:
                for param_id in param_ids_list:
                    try:
                        param_preset = ewes_client.get_engine_param_preset(engine_id, param_id)
                        merge(param_presets, param_preset.preset_values)
                    except Exception as e:
                        raise UnableToFindParameterError(
                            f"Unable to find engine parameter preset with id {param_id}. {e}")

            default_workflow_engine_parameters = param_presets
        else:
            default_workflow_engine_parameters = None

        default_workflow_params = default_workflow_params.parsed_value() if default_workflow_params else {}

        batch_request: BatchRunRequest = BatchRunRequest(
            workflow_url=workflow_url,
            workflow_type="WDL",
            engine_id=engine_id,
            default_workflow_engine_parameters=default_workflow_engine_parameters,
            default_workflow_params=default_workflow_params,
            default_tags=tags.parsed_value() if tags else None,
            run_requests=list(),
            samples=parse_samples()
        )

        for run_request in run_requests:
            parsed_value = run_request.parsed_value() if run_request else None
            parsed_run_request = ExtendedRunRequest(**parsed_value)
            batch_request.run_requests.append(parsed_run_request)

        for workflow_param in workflow_params:
            run_request = ExtendedRunRequest(
                workflow_params=workflow_param.parsed_value() if workflow_param else None
            )
            batch_request.run_requests.append(run_request)

        override_data = parse_and_merge_arguments(input_overrides)
        if override_data:
            if not batch_request.default_workflow_params:
                batch_request.default_workflow_params = dict()
            merge(batch_request.default_workflow_params, override_data)

            for run_request in batch_request.run_requests:
                if not run_request.workflow_params:
                    run_request.workflow_params = dict()
                merge(run_request.workflow_params, override_data)

        if dry_run:
            click.echo(to_json(normalize(batch_request)))
        else:
            minimal_batch = ewes_client.submit_batch(batch_request)
            click.echo(to_json(normalize(minimal_batch)))
