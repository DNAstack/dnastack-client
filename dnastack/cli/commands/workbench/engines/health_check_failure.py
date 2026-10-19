"""Shows an engine's failed health check as a list of checks, as the Workbench UI does, instead of raw JSON."""
from typing import List, Optional

import click

from dnastack.cli.commands.workbench.engines.secret_redaction import redact_text
from dnastack.client.workbench.ewes.models import Check, Outcome
from dnastack.http.session import ClientError


def health_check_report(engine_id: str,
                        action: str,
                        checks: List[Check],
                        trace_id: Optional[str],
                        secrets: Optional[List[str]] = None) -> str:
    """The outcome word is always printed, so the report still reads correctly without colour or symbols.

    Each check's error is service text that may echo the request, so the request's secrets are masked in it.
    """
    width = max(len(check.type.value) for check in checks)
    lines = [f"Engine '{engine_id}' failed its health check and was not {action}.", '']
    for check in checks:
        passed = check.outcome == Outcome.SUCCESS
        line = f"  {'✓' if passed else '✗'} {check.outcome.value}  {check.type.value:<{width}}"
        line = f'{line}  {redact_text(check.error, secrets or [])}' if check.error else line.rstrip()
        lines.append(click.style(line, dim=True) if passed else click.style(line, fg='red'))
    lines += ['', 'Fix the engine description and run the command again.']
    if trace_id:
        lines.append(f'Incident ID {trace_id}')
    return '\n'.join(lines)


def exit_on_failed_health_check(error: ClientError,
                                engine_id: str,
                                action: str,
                                secrets: Optional[List[str]] = None) -> None:
    """Print the report and exit if the error is a failed health check; otherwise return so it is raised as usual.

    secrets are the values the request sent that must not be printed.
    """
    if error.response.status_code != 400:
        return
    try:
        body = error.response.json()
        checks = [Check(**check) for entry in body.get('errors') or [] for check in entry.get('checks') or []]
    except (ValueError, TypeError, AttributeError):
        # Not the health check failure shape (pydantic's ValidationError is a ValueError).
        return
    if not checks:
        return
    click.echo(health_check_report(engine_id, action, checks, body.get('trace_id'), secrets), err=True)
    # SystemExit passes through formatted_command, so the report is not followed by the raw error.
    raise SystemExit(1)
