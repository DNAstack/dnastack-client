import re
from typing import Optional

import click
from click import style

from dnastack.cli.commands.workbench.storage.utils import validate_and_load_service_account_json, \
    handle_sensitive_azure_params
from dnastack.cli.commands.workbench.utils import get_storage_client, NAMESPACE_ARG
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import ArgumentSpec, ArgumentType, CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG
from dnastack.cli.core.group import formatted_group
from dnastack.cli.helpers.exporter import to_json, normalize
from dnastack.client.workbench.storage.models import AwsStorageAccountCredentials, StorageAccount, Provider, \
    GcpStorageAccountCredentials, AzureStorageAccountCredentials, AzureCredentialsType


@formatted_group("add")
def add_storage_command_group():
    """Add storage account"""


@formatted_command(
    group=add_storage_command_group,
    name='aws',
    specs=[
        ArgumentSpec(
            name='storage_id',
            arg_type=ArgumentType.POSITIONAL,
            help='The storage account id',
            required=False,
        ),
        NAMESPACE_ARG,
        ArgumentSpec(
            name='name',
            arg_names=['--name'],
            help='A human readable name for the storage account',
            required=True,
        ),
        ArgumentSpec(
            name='access_key_id',
            arg_names=['--access-key-id'],
            help='The access key id for the storage account to use when authenticating with AWS',
            required=True,
        ),
        ArgumentSpec(
            name='secret_access_key',
            arg_names=['--secret-access-key'],
            help='The Secret Access key for the storage account to use when authenticating with AWS',
            required=True,
        ),
        ArgumentSpec(
            name='region',
            arg_names=['--region'],
            help='The region for the storage account',
            required=True,
        ),
        ArgumentSpec(
            name='bucket',
            arg_names=['--bucket'],
            help='The name of the bucket to use for the storage account',
            required=True,
        ),
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ]
)
def add_aws_storage_account(context: Optional[str],
                            endpoint_id: Optional[str],
                            namespace: Optional[str],
                            storage_id: Optional[str],
                            name: str,
                            access_key_id: str,
                            secret_access_key: str,
                            region: str,
                            bucket: str):
    # Validate bucket format
    if not re.match(r'^s3://', bucket):
        click.echo(style("Error: Bucket name must start with 's3://'", fg='red'), err=True, color=True)
        exit(1)

    """Create a new aws storage account"""
    credentials = AwsStorageAccountCredentials(
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        region=region,
    )
    storage_account = StorageAccount(
        id=storage_id,
        name=name,
        provider=Provider.aws,
        bucket=bucket,
        credentials=credentials
    )

    client = get_storage_client(context, endpoint_id, namespace)
    response = client.add_storage_account(storage_account)
    click.echo(to_json(normalize(response)))


@formatted_command(
    group=add_storage_command_group,
    name='gcp',
    specs=[
        ArgumentSpec(
            name='storage_id',
            arg_type=ArgumentType.POSITIONAL,
            help='The storage account id',
            required=False,
        ),
        NAMESPACE_ARG,
        ArgumentSpec(
            name='name',
            arg_names=['--name'],
            help='A human readable name for the storage account',
            required=True,
        ),
        ArgumentSpec(
            name='service_account_json',
            arg_names=['--service-account'],
            help='The json file for the storage account to use when authenticating with GCP. '
                 'Use @<path> to load from a file.',
            required=True,
        ),
        ArgumentSpec(
            name='region',
            arg_names=['--region'],
            help='The region for the storage account',
            required=True,
        ),
        ArgumentSpec(
            name='project_id',
            arg_names=['--project-id'],
            help='The id of the GCP project',
            required=True,
        ),
        ArgumentSpec(
            name='bucket',
            arg_names=['--bucket'],
            help='The name of the bucket to use for the storage account',
            required=True,
        ),
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ]
)
def add_gcp_storage_account(context: Optional[str],
                            endpoint_id: Optional[str],
                            namespace: Optional[str],
                            storage_id: Optional[str],
                            name: str,
                            service_account_json: str,
                            bucket: str,
                            region: str,
                            project_id: str):
    """Create a new GCP storage account"""

    loaded_service_account = validate_and_load_service_account_json(service_account_json)
    credentials = GcpStorageAccountCredentials(
        service_account_json=loaded_service_account,
        region=region,
        project_id=project_id
    )
    storage_account = StorageAccount(
        id=storage_id,
        name=name,
        provider=Provider.gcp,
        bucket=bucket,
        credentials=credentials
    )

    client = get_storage_client(context, endpoint_id, namespace)
    response = client.add_storage_account(storage_account)
    click.echo(to_json(normalize(response)))


@formatted_command(
    group=add_storage_command_group,
    name='azure',
    specs=[
        ArgumentSpec(
            name='storage_id',
            arg_type=ArgumentType.POSITIONAL,
            help='The storage account id',
            required=False,
        ),
        NAMESPACE_ARG,
        ArgumentSpec(
            name='name',
            arg_names=['--name'],
            help='A human readable name for the storage account',
            required=True,
        ),
        ArgumentSpec(
            name='container',
            arg_names=['--container'],
            help='The name of the blob container',
            required=True,
        ),
        ArgumentSpec(
            name='storage_account_name',
            arg_names=['--storage-account-name'],
            help='The Azure storage account\'s name',
            required=True,
        ),
        ArgumentSpec(
            name='sas',
            arg_names=['--sas'],
            help='The Shared Access Signature (SAS) for secure access. Use @<path> to load from file.',
            required=False,
        ),
        ArgumentSpec(
            name='access_key',
            arg_names=['--access-key'],
            help='The access key for the storage account. Use @<path> to load from file.',
            required=False,
        ),
        ArgumentSpec(
            name='tenant_id',
            arg_names=['--tenant-id'],
            help='Refers to the Azure Active Directory (AAD) tenant associated with the storage account. '
                 'The tenant ID uniquely identifies your organization’s AAD instance.',
            required=False,
        ),
        ArgumentSpec(
            name='client_id',
            arg_names=['--client-id'],
            help='Refers to the application ID of the Azure AD service principal. '
                 'The client ID identifies the application or service trying to access the storage.',
            required=False,
        ),
        ArgumentSpec(
            name='client_secret',
            arg_names=['--client-secret'],
            help='Refers to the password or secret key for the service principal. Use @<path> to load from file.',
            required=False,
        ),
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ]
)
@handle_sensitive_azure_params()
def add_azure_storage_account(context: Optional[str],
                              endpoint_id: Optional[str],
                              namespace: Optional[str],
                              storage_id: Optional[str],
                              name: str,
                              container: str,
                              storage_account_name: str,
                              sas: Optional[str],
                              access_key: Optional[str],
                              tenant_id: Optional[str],
                              client_id: Optional[str],
                              client_secret: Optional[str]):
    """Create a new azure storage account"""
    credentials_type = None
    if sas:
        credentials_type = AzureCredentialsType.SAS_URL
    elif access_key:
        credentials_type = AzureCredentialsType.ACCESS_KEY
    elif tenant_id and client_id and client_secret:
        credentials_type = AzureCredentialsType.CLIENT_CREDENTIALS
    else:
        raise click.BadParameter('Invalid Azure credentials provided. Please provide either SAS, access key, or service principal credentials.')

    credentials = AzureStorageAccountCredentials(
        sas_url=sas,
        access_key=access_key,
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
        storage_account_name=storage_account_name,
        azure_credentials_type=credentials_type
    )
    storage_account = StorageAccount(
        id=storage_id,
        name=name,
        provider=Provider.azure,
        bucket=container,
        credentials=credentials
    )

    client = get_storage_client(context, endpoint_id, namespace)
    response = client.add_storage_account(storage_account)
    click.echo(to_json(normalize(response)))
