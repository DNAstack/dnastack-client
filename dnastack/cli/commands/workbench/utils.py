
from typing import Optional

from imagination import container

from dnastack.cli.commands.config.contexts import ContextCommandHandler
from dnastack.cli.core.command_spec import ArgumentSpec
from dnastack.cli.helpers.client_factory import ConfigurationBasedClientFactory
from dnastack.client.workbench.ewes.client import EWesClient
from dnastack.client.workbench.samples.client import SamplesClient
from dnastack.client.workbench.storage.client import StorageClient
from dnastack.client.workbench.workbench_user_service.client import WorkbenchUserClient

DEFAULT_WORKBENCH_DESTINATION = "workbench.omics.ai"


NAMESPACE_ARG = ArgumentSpec(
    name='namespace',
    arg_names=['--namespace', '-n'],
    help='Specify the namespace to connect to. By default, the namespace will be '
         'extracted from the users credentials.',
)

def create_sort_arg(example: str) -> ArgumentSpec:
    return ArgumentSpec(
        name='sort',
        arg_names=['--sort'],
        help=f'Define how results are sorted. The value should be in the form `column(:direction)?(;(column(:direction)?)*`. '
             f'If no directions are specified, the results are returned in ascending order. '
             f'To change the direction of ordering include the "ASC" or "DESC" string after the column. '
             f'e.g.: {example}',
    )

def _populate_workbench_endpoint():
    handler: ContextCommandHandler = container.get(ContextCommandHandler)
    handler.use(DEFAULT_WORKBENCH_DESTINATION, context_name="workbench", no_auth=False)


def get_user_client(context_name: Optional[str] = None,
                    endpoint_id: Optional[str] = None) -> WorkbenchUserClient:
    factory: ConfigurationBasedClientFactory = container.get(ConfigurationBasedClientFactory)
    try:
        return factory.get(WorkbenchUserClient, endpoint_id=endpoint_id, context_name=context_name)
    except AssertionError:
        _populate_workbench_endpoint()
        return factory.get(WorkbenchUserClient, endpoint_id=endpoint_id, context_name=context_name)


def get_ewes_client(context_name: Optional[str] = None,
                    endpoint_id: Optional[str] = None,
                    namespace: Optional[str] = None) -> EWesClient:
    if not namespace:
        user_client = get_user_client(context_name=context_name, endpoint_id=endpoint_id)
        namespace = user_client.get_user_config().default_namespace

    factory: ConfigurationBasedClientFactory = container.get(ConfigurationBasedClientFactory)
    try:
        return factory.get(EWesClient, endpoint_id=endpoint_id, context_name=context_name, namespace=namespace)
    except AssertionError:
        _populate_workbench_endpoint()
        return factory.get(EWesClient, endpoint_id=endpoint_id, context_name=context_name, namespace=namespace)


def get_samples_client(context_name: Optional[str] = None,
                       endpoint_id: Optional[str] = None,
                       namespace: Optional[str] = None) -> SamplesClient:
    if not namespace:
        user_client = get_user_client(context_name=context_name, endpoint_id=endpoint_id)
        namespace = user_client.get_user_config().default_namespace
    factory: ConfigurationBasedClientFactory = container.get(ConfigurationBasedClientFactory)
    try:
        return factory.get(SamplesClient, endpoint_id=endpoint_id, context_name=context_name, namespace=namespace)
    except AssertionError:
        _populate_workbench_endpoint()
        return factory.get(SamplesClient, endpoint_id=endpoint_id, context_name=context_name, namespace=namespace)


def get_storage_client(context_name: Optional[str] = None,
                       endpoint_id: Optional[str] = None,
                       namespace: Optional[str] = None) -> StorageClient:
    if not namespace:
        user_client = get_user_client(context_name=context_name, endpoint_id=endpoint_id)
        namespace = user_client.get_user_config().default_namespace
    factory: ConfigurationBasedClientFactory = container.get(ConfigurationBasedClientFactory)
    try:
        return factory.get(StorageClient, endpoint_id=endpoint_id, context_name=context_name, namespace=namespace)
    except AssertionError:
        _populate_workbench_endpoint()
        return factory.get(StorageClient, endpoint_id=endpoint_id, context_name=context_name, namespace=namespace)















