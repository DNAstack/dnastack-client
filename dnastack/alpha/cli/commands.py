from typing import List, Optional, Union

from click import Abort
from imagination import container

from dnastack.alpha.cli.auth import alpha_auth_command_group
from dnastack.alpha.cli.collections import alpha_collection_command_group
from dnastack.alpha.cli.data_connect import alpha_data_connect_command_group
from dnastack.alpha.cli.wes import alpha_wes_command_group
from dnastack.cli.commands.collections.utils import COLLECTION_ID_CLI_ARG, _abort_with_collection_list
from dnastack.cli.commands.dataconnect.utils import DECIMAL_POINT_OUTPUT_ARG, handle_query
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import DATA_OUTPUT_ARG
from dnastack.cli.core.group import formatted_group
from dnastack.client.collections.client import (
    EXPLORER_COLLECTION_SERVICE_TYPE_V1_0,
    CollectionServiceClient,
    UnknownCollectionError,
)
from dnastack.client.data_connect import DataConnectClient
from dnastack.client.models import ServiceEndpoint
from dnastack.common.simple_stream import SimpleStream
from dnastack.common.tracing import Span
from dnastack.configuration.manager import ConfigurationManager
from dnastack.configuration.models import DEFAULT_CONTEXT
from dnastack.context.models import Context


@formatted_group("alpha")
def alpha_command_group():
    """
    Interact with experimental commands.

    Warning: Commands in the alpha group are still under development and are being made available for testing and
    feedback. These commands may change incompatibly or be removed entirely at any time.
    """


###############
# Subcommands #
###############
alpha_command_group.add_command(alpha_auth_command_group)
alpha_command_group.add_command(alpha_wes_command_group)
alpha_command_group.add_command(alpha_collection_command_group)
alpha_command_group.add_command(alpha_data_connect_command_group)


#######################
# Root-level commands #
#######################
@formatted_command(
    group=alpha_command_group,
    name="query",
    specs=[
        COLLECTION_ID_CLI_ARG,
        DATA_OUTPUT_ARG,
        DECIMAL_POINT_OUTPUT_ARG,
    ],
)
def run_query(
    context: Optional[str],
    endpoint_id: Optional[str],
    collection: Optional[str],
    query: str,
    output: Optional[str] = None,
    decimal_as: str = "string",
    no_auth: bool = False,
):
    """
    Query the data from the first known Explorer, Publisher Data Service, or Data Connect Service.

    This command assume that the active context is set up via the "use" command and will use Explorer, before falling
    back to Publisher Data Service, and Data Connect Service respectively.

    WARNING: This is an experimental feature and untested. There is no guarantee on the quality or functionality here,
             and you are using at your own risk.
    """
    trace = Span(origin="alpha.cli.query")
    config_manager: ConfigurationManager = container.get(ConfigurationManager)

    # Get the configuration context
    config = config_manager.load()
    context_name = context or config.current_context

    assert context_name is not None, f"The requested context ({context_name}) is not defined."

    if context_name == DEFAULT_CONTEXT and DEFAULT_CONTEXT not in config.contexts:
        config.contexts[DEFAULT_CONTEXT] = Context()

    assert context_name in config.contexts, (
        f"The requested context ({context_name}) is defined but the context is not in the configuration file."
        f" (contexts: {config.contexts.keys()})"
    )

    target_context = config.contexts[context_name]

    # Get the service client and initiate the query.
    client_stream = (
        SimpleStream(target_context.endpoints).filter(_is_data_connect_capable).map(_convert_to_service_client)
    )

    if endpoint_id:
        client_stream.filter(lambda e: e.id == endpoint_id)

    discovery_order: List[Union[CollectionServiceClient, DataConnectClient]] = client_stream.to_list()
    discovery_order.sort(key=lambda c: -1 if isinstance(c, CollectionServiceClient) else 1)

    if discovery_order:
        discovered_client = discovery_order[0]

        # NOTE: Generally, no normal Python developers would preemptively declare the variable type as the scope of
        #       local variable is always for the whole function. This programming pattern is mainly for ease of reading.
        if isinstance(discovered_client, CollectionServiceClient):
            if discovered_client.endpoint.type == EXPLORER_COLLECTION_SERVICE_TYPE_V1_0:
                try:
                    active_collection = discovered_client.get(collection)
                except UnknownCollectionError:
                    _abort_with_collection_list(discovered_client, collection, no_auth=no_auth)

                endpoint: ServiceEndpoint = discovered_client.data_connect_endpoint(
                    collection=active_collection, no_auth=no_auth
                )
            else:
                endpoint: ServiceEndpoint = discovered_client.data_connect_endpoint(no_auth=no_auth)

            data_connect_client: DataConnectClient = DataConnectClient.make(endpoint)
        else:
            data_connect_client: DataConnectClient = discovered_client

        return handle_query(
            data_connect_client,
            query,
            decimal_as=decimal_as,
            no_auth=no_auth,
            output_format=output,
            allow_using_query_from_file=True,
            trace=trace,
        )
    else:
        raise Abort("No Explorer, Publisher Data Service, or Data Connect Service configured for your client")


def _is_data_connect_capable(e: ServiceEndpoint) -> bool:
    return (
        e.type in CollectionServiceClient.get_supported_service_types()
        or e.type in DataConnectClient.get_supported_service_types()
    )


def _convert_to_service_client(e: ServiceEndpoint) -> Union[CollectionServiceClient, DataConnectClient]:
    if e.type in CollectionServiceClient.get_supported_service_types():
        return CollectionServiceClient.make(e)
    elif e.type in DataConnectClient.get_supported_service_types():
        return DataConnectClient.make(e)
    else:
        raise RuntimeError(f"Unable to instantiate a usable service client with {e}")
