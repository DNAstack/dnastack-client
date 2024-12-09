from pathlib import Path
from typing import Optional

import click


def handle_value_or_file(value: Optional[str], param_name: str) -> str:
    """
    Handle parameter values that can be provided directly or loaded from a file using @ prefix.

    Args:
        value: The parameter value, either direct value or file path starting with @
        param_name: Name of the parameter for error messages

    Returns:
        str: The value, either direct or loaded from file

    Raises:
        click.BadParameter: If value is missing or file handling fails
    """
    if value is None:
        raise click.BadParameter(f'{param_name} value is required')

    # Handle file path
    if value.startswith('@'):
        try:
            file_content = Path(value[1:]).read_text().strip()
            if not file_content:
                raise click.BadParameter(f'{param_name} file is empty')
            return file_content
        except FileNotFoundError:
            raise click.BadParameter(f'File not found: {value[1:]}')
        except Exception as e:
            raise click.BadParameter(f'Failed to read {param_name} from file: {e}')

    return value
