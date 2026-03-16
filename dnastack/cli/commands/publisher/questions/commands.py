from typing import Optional

import click
from click import Group

from dnastack.cli.commands.publisher.questions.utils import (
    get_collection_service_client,
    validate_question_parameters,
    handle_question_results_output
)
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import (
    ArgumentSpec,
    ArgumentType,
    CONTEXT_ARG,
    SINGLE_ENDPOINT_ID_ARG,
    RESOURCE_OUTPUT_ARG,
    DATA_OUTPUT_ARG
)
from dnastack.common.json_argument_parser import JsonLike, parse_and_merge_arguments
from dnastack.cli.helpers.iterator_printer import show_iterator
from dnastack.common.logger import get_logger
from dnastack.common.tracing import Span

logger = get_logger(__name__)


def init_questions_commands(group: Group):
    @formatted_command(
        group=group,
        name='list',
        specs=[
            ArgumentSpec(
                name='collection',
                arg_names=['--collection', '-c'],
                help='Collection ID or slug name',
                required=True
            ),
            RESOURCE_OUTPUT_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def list_questions(collection: str, output: str, context: Optional[str], endpoint_id: Optional[str]):
        """List all questions for a collection"""
        trace = Span()
        client = get_collection_service_client(context=context, endpoint_id=endpoint_id)

        questions = client.list_questions(collection, trace=trace)

        show_iterator(
            output_format=output,
            iterator=questions,
            transform=lambda q: q.model_dump()
        )

    @formatted_command(
        group=group,
        name='describe',
        specs=[
            ArgumentSpec(
                name='question_id',
                arg_type=ArgumentType.POSITIONAL,
                help='Question ID to describe',
                required=True
            ),
            ArgumentSpec(
                name='collection',
                arg_names=['--collection', '-c'],
                help='Collection ID or slug name',
                required=True
            ),
            RESOURCE_OUTPUT_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def describe_question(
        question_id: str,
        collection: str,
        output: str,
        context: Optional[str],
        endpoint_id: Optional[str]
    ):
        """Get detailed information about a question"""
        trace = Span()
        client = get_collection_service_client(context=context, endpoint_id=endpoint_id)

        question = client.get_question(collection, question_id, trace=trace)

        show_iterator(
            output_format=output,
            iterator=[question],
            transform=lambda q: q.model_dump()
        )

    @formatted_command(
        group=group,
        name='ask',
        specs=[
            ArgumentSpec(
                name='question_name',
                arg_names=['--question-name'],
                help='Question ID to execute',
                required=True
            ),
            ArgumentSpec(
                name='collection',
                arg_names=['--collection', '-c'],
                help='Collection ID or slug name',
                required=True
            ),
            ArgumentSpec(
                name='args',
                arg_names=['--param'],
                help='Question parameters in key=value format (can be used multiple times)',
                type=JsonLike,
                multiple=True
            ),
            ArgumentSpec(
                name='output_file',
                arg_names=['--output-file'],
                help='Output file path for results'
            ),
            DATA_OUTPUT_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def ask_question(
        question_name: str,
        collection: str,
        args: tuple,
        output_file: Optional[str],
        output: str,
        context: Optional[str],
        endpoint_id: Optional[str]
    ):
        """Execute a question with parameters"""
        trace = Span()
        client = get_collection_service_client(context=context, endpoint_id=endpoint_id)

        # Parse parameters
        inputs = {}
        if args:
            for arg in args:
                parsed_args = arg.parsed_value() if hasattr(arg, 'parsed_value') else parse_and_merge_arguments(arg)
                inputs.update(parsed_args)

        # Get question details for validation
        question = client.get_question(collection, question_name, trace=trace)

        # Validate parameters
        try:
            inputs = validate_question_parameters(inputs, question)
        except ValueError as e:
            click.echo(f"Error: {e}", err=True)
            raise click.Abort()

        # Execute the question
        results_iter = client.ask_question(collection, question_name, inputs, trace=trace)

        # Collect results
        results = list(results_iter)

        # Output results
        handle_question_results_output(results, output_file, output)
