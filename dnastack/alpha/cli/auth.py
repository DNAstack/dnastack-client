import base64
import json
import lzma
from typing import List, Optional

import click
from pydantic import BaseModel, Field

from dnastack.cli.commands.auth.commands import AuthCommandHandler as StableAuthCommandHandler
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import (
    CONTEXT_ARG,
    MULTIPLE_ENDPOINT_ID_ARG,
    SINGLE_ENDPOINT_ID_ARG,
    ArgumentSpec,
    ArgumentType,
)
from dnastack.cli.core.group import formatted_group
from dnastack.cli.helpers.exporter import normalize, to_json
from dnastack.cli.helpers.printer import echo_result
from dnastack.http.authenticators.abstract import AuthStateStatus
from dnastack.http.session_info import Session


@formatted_group("auth")
def alpha_auth_command_group():
    """Manage authentication and authorization"""


@formatted_command(
    group=alpha_auth_command_group,
    name="export",
    specs=[
        MULTIPLE_ENDPOINT_ID_ARG,
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ],
)
def export_backup(
    context: Optional[str], endpoint_id: Optional[str] = None, pretty: bool = False, compress: bool = False
):
    """Export sessions"""
    handler = AuthCommandHandler(context_name=context)
    endpoint_ids = endpoint_id.strip().split(",") if (endpoint_id and endpoint_id.strip()) else None
    result = to_json(normalize(handler.create_backup(endpoint_ids)), indent=2 if pretty else None)
    if compress:
        result = base64.b64encode(lzma.compress(result.encode("utf-8")))
    click.echo(result)


@formatted_command(
    group=alpha_auth_command_group,
    name="import",
    specs=[
        ArgumentSpec(
            name="backup_content",
            arg_type=ArgumentType.POSITIONAL,
            help="The backup content to import.",
            required=True,
        ),
        CONTEXT_ARG,
    ],
)
def import_from_backup(context: Optional[str], backup_content: str):
    """Import sessions"""
    content = backup_content.strip()
    if content[0] != r"{":
        content = lzma.decompress(base64.b64decode(content))
    backup = SessionBackup(**json.loads(content))

    handler = AuthCommandHandler(context_name=context)
    handler.restore_backup(backup)


class SessionEntry(BaseModel):
    id: str
    session: Optional[Session] = None
    endpoints: List[str] = Field(default_factory=list)


class SessionBackup(BaseModel):
    dnastack_schema_version: float = Field(alias="model_version", default=1.0)
    sessions: List[SessionEntry] = Field(default_factory=list)


class AuthCommandHandler(StableAuthCommandHandler):
    def create_backup(self, endpoint_ids: List[str]) -> SessionBackup:
        backup = SessionBackup()
        for state in self._auth_manager.get_states(endpoint_ids):
            if state.status in [AuthStateStatus.READY, AuthStateStatus.REFRESH_REQUIRED]:
                entry = SessionEntry(id=state.id, session=state.session_info, endpoints=state.endpoints)
                backup.sessions.append(entry)
                echo_result("Session", "green", "Exported", f"Session for {', '.join(state.endpoints)}")
            else:
                echo_result("Session", "red", "Ignored", f"Session for {', '.join(state.endpoints)} ({state.status})")
        return backup

    def restore_backup(self, backup: SessionBackup):
        for entry in backup.sessions:
            echo_result("Session", "green", "Restored", f"Session for {', '.join(entry.endpoints)}")
            self._session_manager.save(entry.id, entry.session)
