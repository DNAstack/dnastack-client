import json
import os
from typing import Optional

import click
from click import style

from dnastack.client.workbench.storage.models import AzureCredentialsType
from dnastack.common.json_argument_parser import FileOrValue


def validate_and_load_service_account_json(service_account_json: str) -> str:
    if not service_account_json.startswith("@"):
        click.echo(
            style("Error: Service account JSON must be a file path starting with '@'", fg="red"), err=True, color=True
        )
        exit(1)
    service_account_json_file_path = service_account_json[1:]
    if not os.path.isfile(service_account_json_file_path):
        click.echo(
            style(f"Error: File '{service_account_json_file_path}' does not exist.", fg="red"), err=True, color=True
        )
        exit(1)

    try:
        with open(service_account_json_file_path) as f:
            service_account = json.load(f)
    except json.JSONDecodeError:
        click.echo(style("Error: Malformed service account JSON.", fg="red"), err=True, color=True)
        exit(1)
    except Exception as e:
        click.echo(style(f"Error: {str(e)}", fg="red"), err=True, color=True)
        exit(1)

    # return service_account
    return json.dumps(service_account)


def validate_azure_credentials(
    sas: Optional[FileOrValue],
    access_key: Optional[FileOrValue],
    tenant_id: Optional[str],
    client_id: Optional[str],
    client_secret: Optional[FileOrValue],
) -> AzureCredentialsType:
    """
    Validate Azure storage account authentication parameters and return the appropriate credentials type.

    Args:
        sas: Optional shared access signature
        access_key: Optional access key
        tenant_id: Optional tenant ID for service principal auth
        client_id: Optional client ID for service principal auth
        client_secret: Optional client secret for service principal auth

    Returns:
        AzureCredentialsType indicating the validated authentication method

    Raises:
        ValueError: If invalid or conflicting authentication parameters are provided
    """
    # Track which auth methods have parameters provided
    auth_methods = {
        "sas": bool(sas),
        "access_key": bool(access_key),
        "service_principal": any([tenant_id, client_id, client_secret]),
    }

    # Count how many auth methods were provided
    provided_methods = [method for method, is_provided in auth_methods.items() if is_provided]

    if len(provided_methods) > 1:
        raise ValueError(f"Conflicting authentication methods provided: {', '.join(provided_methods)}. Use only one.")

    if len(provided_methods) == 0:
        raise ValueError(
            "No authentication method provided. Use either SAS, access key, or service principal credentials."
        )

    # Map the provided method to the appropriate credential type
    credentials_type_map = {
        "sas": AzureCredentialsType.SAS_URL,
        "access_key": AzureCredentialsType.ACCESS_KEY,
        "service_principal": AzureCredentialsType.CLIENT_CREDENTIALS,
    }

    return credentials_type_map[provided_methods[0]]
