from traceback import print_exc
from typing import Callable, List, Optional

import click
from click import Group

from dnastack.cli.core.group_formatting import FormattedHelpGroup
from dnastack.common.logger import get_logger
from dnastack.common.tracing import Span
from dnastack.feature_flags import currently_in_debug_mode, show_distributed_trace_stack_on_error


def formatted_group(
    name: str, help_text: Optional[str] = None, hidden: bool = False, aliases: Optional[List[str]] = None
):
    """
    Decorator that creates a CLI group with formatted help output.

    Args:
        name: Name of the command group
        help_text: Help text for the group
        hidden: Whether to hide the group from help output
        aliases: Optional list of alternative names for the group
    """

    def decorator(f: Callable) -> Group:
        # Set up logging
        _logger = get_logger(f"@formatted_group/{name}")

        # Create the group with formatted help
        cmd = FormattedHelpGroup(name=name, callback=f, help=help_text or f.__doc__, hidden=hidden, aliases=aliases)

        def handle_invocation(*args, **kwargs):
            """Wrapper to handle errors and tracing"""
            if currently_in_debug_mode():
                try:
                    f(*args, **kwargs)
                except Exception as e:

                    def _printer(msg: str):
                        click.secho(msg, dim=True, err=True)

                    if hasattr(e, "trace"):
                        e.trace.print_tree(external_printer=_printer)

                    raise e
            else:
                try:
                    f(*args, **kwargs)
                except (OSError, TypeError, AttributeError, IndexError, KeyError) as e:
                    click.secho("Unexpected programming error", fg="red", err=True)
                    print_exc()
                    raise SystemExit(1) from e
                except Exception as e:
                    error_type = type(e).__name__
                    click.secho(f"{error_type}: ", fg="red", bold=True, nl=False, err=True)
                    click.secho(str(e), fg="red", err=True)

                    if hasattr(e, "trace"):
                        trace: Span = e.trace
                        click.secho(f"Incident ID {trace.trace_id}", dim=True, err=True)

                        def _printer(msg: str):
                            click.secho(msg, dim=True, err=True)

                        if show_distributed_trace_stack_on_error:
                            trace.print_tree(external_printer=_printer)
                        else:
                            _logger.debug(
                                "Set DNASTACK_DISPLAY_TRACE_ON_ERROR (environment variable) "
                                'to "true" for the trace information without the debug mode'
                            )

                    raise SystemExit(1) from e

        # Replace the callback with our error-handling version
        cmd.callback = handle_invocation

        _logger.debug(f"Group {name} setup complete")

        return cmd

    return decorator
