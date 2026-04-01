import re
from enum import Enum
from typing import List, Optional, Union, Any, Type

from pydantic import BaseModel, Field

from dnastack.cli.helpers.iterator_printer import OutputFormat


class ArgumentType(Enum):
    POSITIONAL = "positional"
    OPTION = "option"


class ArgumentSpec(BaseModel):
    """
    Specification for a command argument.

    Args:
        name: Argument name (used as variable name in the function)
        arg_names: List of argument names (for options: ['--name', '-n'], for positional: ['name'])
        arg_type: ArgumentType.POSITIONAL or ArgumentType.OPTION
        help: Help text description
        required: Whether the argument is required
        default: Default value
        type: Type of the argument (str, int, etc.)
        multiple: Whether the argument can accept multiple values
        choices: List of valid choices for the argument
        ignored: Whether to ignore this argument in command processing
        hidden: Whether to hide this option from --help output (option still works when invoked)
    """
    name: str
    arg_names: Optional[List[str]] = Field(default_factory=list)
    arg_type: ArgumentType = ArgumentType.OPTION
    help: Optional[str] = None
    choices: Optional[List] = Field(default_factory=list)
    ignored: bool = False
    hidden: bool = False
    multiple: bool = False
    nargs: Optional[Union[int, str]] = None
    type: Optional[Type] = None  # WARNING: This will override the parameter reflection.
    default: Optional[Any] = None  # WARNING: This will override the parameter reflection.
    required: Optional[bool] = None  # WARNING: This will override the parameter reflection.

    def get_argument_names(self) -> List[str]:
        """Get the list of argument names, generating them if not explicitly provided."""
        if self.arg_names:
            return self.arg_names

        # Generate argument names based on the argument type
        if self.arg_type == ArgumentType.POSITIONAL:
            # For positional arguments, just use the name (converted to kebab-case)
            kebab_name = re.sub(r'_', '-', self.name)
            return [kebab_name]
        else:
            # For options, create the long form
            kebab_name = re.sub(r'_', '-', self.name)
            return [f"--{kebab_name}"]

CONTEXT_ARG = ArgumentSpec(
    name='context',
    arg_names=['--context'],
    help='The context to use. If not provided, the default context will be used.',
)

SINGLE_ENDPOINT_ID_ARG = ArgumentSpec(
    name='endpoint_id',
    arg_names=['--endpoint-id'],
    help='Endpoint ID',
)

MULTIPLE_ENDPOINT_ID_ARG = ArgumentSpec(
    name='endpoint_id',
    arg_names=['--endpoint-id'],
    help='Endpoint IDs, separated by comma, e.g., --endpoint-id=s_1,s_2,...,s_n',
)

RESOURCE_OUTPUT_ARG = ArgumentSpec(
    name='output',
    arg_names=['--output', '-o'],
    choices=[OutputFormat.JSON, OutputFormat.YAML],
    help='Output format',
    default=OutputFormat.JSON,
)

DATA_OUTPUT_ARG = ArgumentSpec(
    name='output',
    arg_names=['--output', '-o'],
    choices=[OutputFormat.CSV, OutputFormat.JSON, OutputFormat.YAML],
    help='Output format',
    default=OutputFormat.JSON,
)
