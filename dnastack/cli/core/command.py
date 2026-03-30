from traceback import print_exc
from typing import List, Any

import click

from dnastack.cli.core.command_formatting import FormattedHelpCommand
from dnastack.cli.core.command_spec import ArgumentType, ArgumentSpec
from dnastack.common.logger import get_logger
from dnastack.common.tracing import Span
from dnastack.feature_flags import currently_in_debug_mode, show_distributed_trace_stack_on_error


def formatted_command(group, name, specs: List[ArgumentSpec], hidden: bool = False):
    """
    Decorator that creates a CLI command with formatted help output.

    Args:
        group: Click group to attach the command to
        name: Name of the command
        specs: List of ArgumentSpec objects defining the command parameters
        hidden: Whether to hide the command from help output
    """
    def decorator(f):
        # Set up logging
        _logger = get_logger(f'@formatted_command/{name}')

        # Create the command first with hidden parameter
        cmd = FormattedHelpCommand(name=name, callback=f, help=f.__doc__, hidden=hidden)

        def handle_invocation(*args, **kwargs) -> Any:
            """Wrapper to handle errors and tracing"""
            result = None

            if currently_in_debug_mode():
                try:
                    result = f(*args, **kwargs)
                    if isinstance(result, Exception):
                        click.echo(str(result), err=True)
                        raise SystemExit(1)
                    return result
                except Exception as e:
                    def _printer(msg: str):
                        click.secho(msg, dim=True, err=True)

                    if hasattr(e, 'trace'):
                        e.trace.print_tree(external_printer=_printer)

                    raise e
            else:
                try:
                    result = f(*args, **kwargs)
                    if isinstance(result, Exception):
                        click.echo(str(result), err=True)
                        raise SystemExit(1)
                    return result
                except (IOError, TypeError, AttributeError, IndexError, KeyError) as e:
                    click.secho('Unexpected programming error', fg='red', err=True)
                    print_exc()
                    raise SystemExit(1) from e
                except Exception as e:
                    error_type = type(e).__name__
                    click.secho(f'{error_type}: ', fg='red', bold=True, nl=False, err=True)
                    click.secho(str(e), fg='red', err=True)

                    if hasattr(e, 'trace'):
                        trace: Span = e.trace
                        click.secho(f'Incident ID {trace.trace_id}', dim=True, err=True)

                        def _printer(msg: str):
                            click.secho(msg, dim=True, err=True)

                        if show_distributed_trace_stack_on_error:
                            trace.print_tree(external_printer=_printer)
                        else:
                            _logger.debug('Set DNASTACK_DISPLAY_TRACE_ON_ERROR (environment variable) '
                                          'to "true" for the trace information without the debug mode')

                    raise SystemExit(1) from e

            return result

        # Replace the callback with our error-handling version
        cmd.callback = handle_invocation

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
                option_kwargs['type'] = click.Choice(spec.choices)
                option_kwargs['show_choices'] = True

            option = click.option(*arg_names, **option_kwargs)
            wrapped_callback = option(wrapped_callback)

        # Get all params from the wrapped callback
        cmd.params = wrapped_callback.__click_params__ if hasattr(wrapped_callback, '__click_params__') else []

        # Update the command's callback
        cmd.callback = wrapped_callback

        # Add the command to the group
        group.add_command(cmd)

        _logger.debug(f'Command {name} setup complete')

        return cmd

    return decorator
