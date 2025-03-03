from typing import TypeVar

from dnastack.client.base_client import BaseServiceClient
from dnastack.client.collections.client import CollectionServiceClient
from dnastack.client.data_connect import DataConnectClient
from dnastack.client.datasources.client import DataSourceServiceClient
from dnastack.client.drs import DrsClient
from dnastack.client.service_registry.client import ServiceRegistry
from dnastack.client.workbench.ewes.client import EWesClient
from dnastack.client.workbench.samples.client import SamplesClient
from dnastack.client.workbench.storage.client import StorageClient
from dnastack.client.workbench.workbench_user_service.client import WorkbenchUserClient
from dnastack.client.workbench.workflow.client import WorkflowClient

# All known client classes
ALL_SERVICE_CLIENT_CLASSES = (
    CollectionServiceClient, DataConnectClient, DrsClient, ServiceRegistry, EWesClient, StorageClient, SamplesClient,
    WorkflowClient,
    WorkbenchUserClient, DataSourceServiceClient)

# All client classes for data access
DATA_SERVICE_CLIENT_CLASSES = (
    CollectionServiceClient, DataConnectClient, DrsClient, EWesClient, StorageClient, WorkflowClient,
    WorkbenchUserClient, DataSourceServiceClient)

# Type variable for the service client
SERVICE_CLIENT_CLASS = TypeVar('SERVICE_CLIENT_CLASS',
                               BaseServiceClient,
                               EWesClient,
                               StorageClient,
                               WorkflowClient,
                               WorkbenchUserClient,
                               CollectionServiceClient,
                               DataConnectClient,
                               DrsClient,
                               SamplesClient,
                               ServiceRegistry,
                               DataSourceServiceClient)
