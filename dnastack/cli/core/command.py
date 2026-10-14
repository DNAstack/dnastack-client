import inspect
from typing import List, Optional

import click

from dnastack.cli.core.command_formatting import FormattedHelpCommand
from dnastack.cli.core.command_spec import ArgumentType, ArgumentSpec
from dnastack.common.logger import get_logger


def formatted_command(group, name, specs: List[ArgumentSpec], hidden: bool = False,
                      required_section_title: Optional[str] = None):
    """
    Decorator that creates a CLI command with formatted help output.

    Args:
        group: Click group to attach the command to
        name: Name of the command
        specs: List of ArgumentSpec objects defining the command parameters
        hidden: Whether to hide the command from help output
        required_section_title: The heading of the required options section in help, instead of
            "Required Options:"
    """
    def decorator(f):
        # Set up logging
        _logger = get_logger(f'@formatted_command/{name}')

        # Create the command first with hidden parameter
        # The help is printed as written, so dedent it to print flush whatever the docstring's indentation.
        cmd = FormattedHelpCommand(name=name, callback=f, help=inspect.cleandoc(f.__doc__) if f.__doc__ else None,
                                   hidden=hidden)
        if required_section_title:
            cmd.required_section_title = required_section_title

        # Create a wrapper function that matches parameter names
        def wrapped_callback(**kwargs):
            try:
                # Create a mapping of CLI option names (both long and short) to function parameter names
                name_mapping = {}
                for spec in specs:
                    if spec.arg_type != ArgumentType.POSITIONAL and spec.arg_names:
                        # Handle all possible argument names for this spec
                        for arg_name in spec.arg_names:
                            # Strip leading dashes and convert to underscore format
                            cli_name = arg_name.lstrip('-').replace('-', '_')
                            # Map both the full and processed names to the spec name
                            name_mapping[cli_name] = spec.name
                            # For long options (--option-name), also map the original format
                            if arg_name.startswith('--'):
                                name_mapping[arg_name[2:].replace('-', '_')] = spec.name

                # Remap the kwargs based on our mapping
                remapped_kwargs = {}
                for key, value in kwargs.items():
                    # Check if this key needs to be remapped
                    if key in name_mapping:
                        remapped_kwargs[name_mapping[key]] = value
                    else:
                        remapped_kwargs[key] = value

                result = f(**remapped_kwargs)
                if isinstance(result, Exception):
                    click.echo(str(result), err=True)
                    raise SystemExit(1)
                return result
            except click.ClickException:
                # Usage and bad-parameter errors: click prints them with the usage line and exits 2.
                raise
            except Exception as e:
                click.secho(f"{type(e).__name__}: {str(e)}", fg='red', err=True)
                raise SystemExit(1) from e

        # Separate positional and option arguments
        positional_specs = [spec for spec in specs if spec.arg_type == ArgumentType.POSITIONAL]
        option_specs = [spec for spec in specs if spec.arg_type != ArgumentType.POSITIONAL]

        # Process positional arguments in forward order to maintain correct ordering
        for spec in positional_specs:
            arg_name = spec.name

            # Set up argument parameters
            arg_params = {
                'type': spec.type,
                'required': spec.required if spec.required is not None else True,
            }

            # Handle multiple values
            if spec.multiple or spec.nargs:
                arg_params['nargs'] = spec.nargs if spec.nargs is not None else -1

            if spec.default is not None:
                arg_params['default'] = spec.default

            # Create the argument
            arg = click.argument(arg_name, **arg_params)
            wrapped_callback = arg(wrapped_callback)

            # Store help text for the argument
            if spec.help:
                cmd.store_argument_help(arg_name, spec.help)

        # Process option arguments (order doesn't matter for these)
        for spec in option_specs:
            # Handle option arguments
            arg_names = spec.get_argument_names()

            # Validate option names
            for arg_name in arg_names:
                if not arg_name.startswith('-'):
                    raise ValueError(f"Invalid option name '{arg_name}'. Must start with - or --")

            # Create option
            option_kwargs = {
                'help': spec.help,
                'required': spec.required if spec.required is not None else False,
                'default': spec.default,
                'type': spec.type,
                'multiple': spec.multiple,
                'hidden': spec.hidden,
            }

            # Add special handling for boolean flags
            if spec.type is bool:
                option_kwargs['is_flag'] = True
                option_kwargs['required'] = False
                option_kwargs['show_default'] = False

            if spec.choices:
                option_kwargs['type'] = click.Choice(spec.choices, case_sensitive=spec.case_sensitive)
                option_kwargs['show_choices'] = True

            option = click.option(*arg_names, **option_kwargs)
            wrapped_callback = option(wrapped_callback)

        # Get all params from the wrapped callback
        cmd.params = wrapped_callback.__click_params__ if hasattr(wrapped_callback, '__click_params__') else []
        for spec in option_specs:
            if spec.common_option or spec.display_required:
                for param in cmd.params:
                    if set(param.opts) & set(spec.get_argument_names()):
                        if spec.common_option:
                            cmd.store_common_option(param.name)
                        if spec.display_required:
                            cmd.store_display_required_option(param.name)
        for spec in option_specs:
            if spec.example_value:
                for param in cmd.params:
                    if set(param.opts) & set(spec.get_argument_names()):
                        cmd.store_example_value(param.name, spec.example_value)

        # Update the command's callback
        cmd.callback = wrapped_callback

        # Add the command to the group
        group.add_command(cmd)

        _logger.debug(f'Command {name} setup complete')

        return cmd

    return decorator
