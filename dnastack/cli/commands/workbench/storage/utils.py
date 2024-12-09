import json
import os
from functools import wraps

import click
from click import style

from dnastack.cli.commands.utils import handle_value_or_file


def validate_and_load_service_account_json(service_account_json: str) -> str:
    if not service_account_json.startswith("@"):
        click.echo(style("Error: Service account JSON must be a file path starting with '@'", fg='red'), err=True, color=True)
        exit(1)
    service_account_json_file_path = service_account_json[1:]
    if not os.path.isfile(service_account_json_file_path):
        click.echo(style(f"Error: File '{service_account_json_file_path}' does not exist.", fg='red'), err=True, color=True)
        exit(1)

    try:
        with open(service_account_json_file_path, 'r') as f:
            service_account = json.load(f)
    except json.JSONDecodeError:
        click.echo(style("Error: Malformed service account JSON.", fg='red'), err=True, color=True)
        exit(1)
    except Exception as e:
        click.echo(style(f"Error: {str(e)}", fg='red'), err=True, color=True)
        exit(1)

    # return service_account
    return json.dumps(service_account)


def handle_sensitive_azure_params():
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # First validate the auth method choice
            ctx = click.get_current_context()
            auth_method = validate_azure_auth_params(ctx, ['sas', 'access_key', 'tenant_id', 'client_id', 'client_secret'])

            # Only process sensitive parameters for the chosen auth method
            if auth_method == 'sas':
                kwargs['sas'] = handle_value_or_file(kwargs.get('sas'), 'sas')
            elif auth_method == 'access_key':
                kwargs['access_key'] = handle_value_or_file(kwargs.get('access_key'), 'access_key')
            elif auth_method == 'service_principal':
                kwargs['client_secret'] = handle_value_or_file(kwargs.get('client_secret'), 'client_secret')

            return f(*args, **kwargs)
        return wrapper
    return decorator


def validate_azure_auth_params(ctx, auth_params):
    """
    Validate authentication parameters and return the chosen auth method.
    Only considers parameters that were explicitly provided in the command.
    """
    # Get parameters that were explicitly provided in the command
    provided = []
    for param in auth_params:
        # Check if parameter exists and wasn't just initialized as None
        param_value = ctx.params.get(param)
        if param_value is not None or (isinstance(param_value, tuple) and len(param_value) == 0):
            provided.append(param)

    auth_methods = {
        'sas': ['sas'],
        'access_key': ['access_key'],
        'service_principal': ['tenant_id', 'client_id', 'client_secret']
    }

    # Check for conflicting auth methods
    conflicting_methods = []
    for method, params in auth_methods.items():
        if any(p in provided for p in params):
            conflicting_methods.append(method)

    if len(conflicting_methods) > 1:
        raise click.BadParameter(
            f'Conflicting authentication methods provided: {", ".join(conflicting_methods)}. Use only one.')

    # Now validate the chosen method
    chosen_method = None
    for method, params in auth_methods.items():
        if any(p in provided for p in params):
            chosen_method = method
            # Verify all required params for this method are present
            if not all(p in provided for p in params):
                missing = [p for p in params if p not in provided]
                raise click.BadParameter(
                    f'{method} auth requires all of: {", ".join(params)}. Missing: {", ".join(missing)}')

    if not chosen_method:
        raise click.BadParameter('No authentication method provided. Use either SAS, access key, or service principal.')

    return chosen_method
