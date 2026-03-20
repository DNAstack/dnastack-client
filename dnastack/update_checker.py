import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

import click
import requests
from packaging.version import Version

from dnastack.common.logger import get_logger
from dnastack.constants import (
    __version__,
    LOCAL_STORAGE_DIRECTORY,
    PYPI_PACKAGE_NAME,
    UPDATE_CHECK_CACHE_FILENAME,
)

_logger = get_logger(__name__)

CACHE_TTL = timedelta(hours=24)
PYPI_URL = f"https://pypi.org/pypi/{PYPI_PACKAGE_NAME}/json"
REQUEST_TIMEOUT_SECONDS = 5

# Flag to prevent double notification when `version` command already did an explicit check
_skip_passive_notification = False


@dataclass
class UpdateCheckResult:
    latest_version: Optional[str]
    update_available: bool
    check_failed: bool


def _get_cache_path() -> str:
    return os.path.join(LOCAL_STORAGE_DIRECTORY, UPDATE_CHECK_CACHE_FILENAME)


def _is_suppressed() -> bool:
    if os.environ.get("DNASTACK_NO_UPDATE_CHECK"):
        return True
    if os.environ.get("CI"):
        return True
    if not sys.stderr.isatty():
        return True
    return False


def _read_cache(cache_path: str) -> Tuple[Optional[str], Optional[datetime]]:
    try:
        with open(cache_path) as f:
            data = json.load(f)
        latest_version = data.get("latest_version")
        last_checked_str = data.get("last_checked")
        if latest_version and last_checked_str:
            last_checked = datetime.fromisoformat(last_checked_str.replace("Z", "+00:00"))
            return latest_version, last_checked
    except Exception:
        _logger.debug("Failed to read update check cache", exc_info=True)
    return None, None


def _write_cache(cache_path: str, latest_version: str) -> None:
    try:
        parent_directory = os.path.dirname(cache_path)
        os.makedirs(parent_directory, exist_ok=True)
        data = {
            "latest_version": latest_version,
            "last_checked": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        with open(cache_path, "w") as f:
            json.dump(data, f)
    except Exception:
        _logger.debug("Failed to write update check cache", exc_info=True)


def _get_latest_stable_version() -> Optional[str]:
    try:
        response = requests.get(PYPI_URL, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
        releases = data.get("releases", {})
        stable_versions = [
            Version(version_string)
            for version_string, files in releases.items()
            if files and not Version(version_string).is_prerelease
        ]
        if not stable_versions:
            return None
        return str(max(stable_versions))
    except Exception:
        _logger.debug("Failed to fetch latest version from PyPI", exc_info=True)
        return None


def check_for_update(force: bool = False) -> UpdateCheckResult:
    cache_path = _get_cache_path()

    if not force:
        cached_version, last_checked = _read_cache(cache_path)
        if cached_version and last_checked:
            cache_age = datetime.now(timezone.utc) - last_checked
            if cache_age < CACHE_TTL:
                current_version = Version(__version__)
                latest_version = Version(cached_version)
                return UpdateCheckResult(
                    latest_version=cached_version,
                    update_available=latest_version > current_version,
                    check_failed=False,
                )

    latest_version_string = _get_latest_stable_version()

    if latest_version_string is None:
        return UpdateCheckResult(latest_version=None, update_available=False, check_failed=True)

    _write_cache(cache_path, latest_version_string)

    current_version = Version(__version__)
    latest_version = Version(latest_version_string)

    return UpdateCheckResult(
        latest_version=latest_version_string,
        update_available=latest_version > current_version,
        check_failed=False,
    )


def suppress_passive_notification() -> None:
    """Call this to prevent the passive result_callback notification from firing.

    Used by the `version` command to avoid double-notifying when an explicit
    check has already been displayed to stdout.
    """
    global _skip_passive_notification
    _skip_passive_notification = True


def notify_if_update_available() -> None:
    global _skip_passive_notification
    if _skip_passive_notification:
        _skip_passive_notification = False
        return

    if _is_suppressed():
        return

    try:
        result = check_for_update(force=False)
        if result.update_available:
            click.secho(
                f"\nA new version of dnastack is available: {__version__} \u2192 {result.latest_version}",
                fg="yellow",
                err=True,
            )
            click.secho(
                f"To upgrade, run: pip install --upgrade {PYPI_PACKAGE_NAME}",
                fg="yellow",
                err=True,
            )
    except Exception:
        _logger.debug("Update notification failed", exc_info=True)
