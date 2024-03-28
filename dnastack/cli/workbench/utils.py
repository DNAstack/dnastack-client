from typing import Optional

from imagination import container

from dnastack.client.workbench.ewes.client import EWesClient
from dnastack.client.workbench.workflow.client import WorkflowClient
from dnastack.client.workbench.workbench_user_service.client import WorkbenchUserClient
from dnastack.cli.config.context import ContextCommandHandler
from dnastack.cli.helpers.client_factory import ConfigurationBasedClientFactory


DEFAULT_WORKBENCH_DESTINATION = "workbench.omics.ai"


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


def get_workflow_client(context_name: Optional[str] = None,
                        endpoint_id: Optional[str] = None,
                        namespace: Optional[str] = None) -> WorkflowClient:
    if not namespace:
        user_client = get_user_client(context_name=context_name, endpoint_id=endpoint_id)
        namespace = user_client.get_user_config().default_namespace

    factory: ConfigurationBasedClientFactory = container.get(ConfigurationBasedClientFactory)
    try:
        return factory.get(WorkflowClient, endpoint_id=endpoint_id, context_name=context_name, namespace=namespace)
    except AssertionError:
        _populate_workbench_endpoint()
        return factory.get(WorkflowClient, endpoint_id=endpoint_id, context_name=context_name, namespace=namespace)




class UnableToMergeJsonError(RuntimeError):
    def __init__(self, key):
        super().__init__(f'Unable to merge key {key}. The value for {key} must be of type dict, str, int or float')


class UnableToFindFileError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class UnableToDecodeFileError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class UnableToDisplayFileError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class IncorrectFlagError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class UnableToCreateFilePathError(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class UnableToWriteToFileError(Exception):
    def __init__(self, message: str):
        super().__init__(message)