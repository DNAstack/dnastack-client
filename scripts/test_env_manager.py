#!/usr/bin/env python3
import os.path
import re
import sys
import tempfile
from subprocess import call
from typing import List

import click
from google.cloud.secretmanager_v1 import SecretVersion

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dnastack.common.secret_repository import SecretNotFound, SecretRepository

BUILD_PROJECT_ID = "cloud-builld-webhook"
RE_VALID_ENV_ID = r"[a-z0-9][a-z0-9_\-]*[a-z0-9]"
SECRET_PREFIX = "cli-test-env"

secrets = SecretRepository(BUILD_PROJECT_ID)


def _get_secret_id(env_id: str):
    assert re.search(RE_VALID_ENV_ID, env_id), f"Invalid environment ID (expected pattern: {RE_VALID_ENV_ID})"
    return f"{SECRET_PREFIX}-{env_id}"


def _list_versions(env_id: str, exit_on_not_found: bool = True) -> List[SecretVersion]:
    secret_id = _get_secret_id(env_id)
    try:
        return secrets.list_versions(secret_id)
    except SecretNotFound as e:
        if exit_on_not_found:
            click.secho(f"Secret {secret_id} does not exist.", err=True, fg="red")
            sys.exit(1)
        else:
            raise e


@click.group()
def app():
    """Test Environment Manager"""


@app.command("list-versions")
@click.argument("env_id")
def list_versions(env_id: str):
    """List all available versions of the secret corresponding to the given test environment"""
    for version in _list_versions(env_id):
        click.secho(f"→ {version.name}")


@app.command()
@click.argument("env_id")
def edit(env_id: str):
    """Edit the test environment with VIM. The environment will be based on the previous version if available."""
    secret_id = _get_secret_id(env_id)
    known_versions = secrets.create_if_not_exist(secret_id)

    latest_version = known_versions[-1] if known_versions else None
    if latest_version:
        click.secho(f"The last known version is {latest_version.name}", err=True, fg="blue")
        current_payload = secrets.get(secret_id)
    else:
        current_payload = ""

    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write(current_payload.encode("UTF-8"))
    temp_file.close()

    click.secho(f"Using the temp file ({temp_file.name})...", dim=True)

    call(["vim", temp_file.name])

    with open(temp_file.name) as f:
        new_version = secrets.set(secret_id, f.read())

    click.secho(f"Removing the temp file ({temp_file.name})...", dim=True)
    os.unlink(temp_file.name)
    click.secho(f"Removed the temp file ({temp_file.name}).", dim=True)

    click.secho(f"New version: ({new_version.name}).", fg="green")


@app.command("copy-from")
@click.argument("env_id")
@click.argument("source_path")
def copy_from(env_id: str, source_path: str):
    """Copy the test environment from file."""
    secret_id = _get_secret_id(env_id)

    secrets.create_if_not_exist(secret_id)

    with open(source_path) as f:
        new_version = secrets.set(secret_id, f.read())

    click.secho(f"New version: ({new_version.name}).", fg="green")


@app.command()
@click.argument("env_id")
def read(env_id: str):
    """Read the test environment."""
    secret_id = _get_secret_id(env_id)
    click.echo(secrets.get(secret_id))


if __name__ == "__main__":
    app()
