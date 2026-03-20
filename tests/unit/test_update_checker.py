import json
import os
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from dnastack.update_checker import (
    UpdateCheckResult,
    _is_suppressed,
    _read_cache,
    _write_cache,
    _get_latest_stable_version,
    check_for_update,
    notify_if_update_available,
    suppress_passive_notification,
)
from dnastack.constants import UPDATE_CHECK_CACHE_FILENAME


class TestUpdateCheckResult:
    """Tests for the UpdateCheckResult dataclass."""

    def test_update_available(self):
        result = UpdateCheckResult(latest_version="3.2.0", update_available=True, check_failed=False)
        assert result.latest_version == "3.2.0"
        assert result.update_available is True
        assert result.check_failed is False

    def test_up_to_date(self):
        result = UpdateCheckResult(latest_version="3.1.0", update_available=False, check_failed=False)
        assert result.latest_version == "3.1.0"
        assert result.update_available is False
        assert result.check_failed is False

    def test_check_failed(self):
        result = UpdateCheckResult(latest_version=None, update_available=False, check_failed=True)
        assert result.latest_version is None
        assert result.update_available is False
        assert result.check_failed is True


class TestSuppression:
    """Tests for the suppression logic."""

    def test_suppressed_when_env_var_set(self):
        with patch.dict(os.environ, {"DNASTACK_NO_UPDATE_CHECK": "1"}):
            assert _is_suppressed() is True

    def test_suppressed_when_ci_env_set(self):
        with patch.dict(os.environ, {"CI": "true"}, clear=False):
            assert _is_suppressed() is True

    def test_suppressed_when_not_tty(self):
        with patch("sys.stderr") as mock_stderr:
            mock_stderr.isatty.return_value = False
            assert _is_suppressed() is True

    def test_not_suppressed_in_interactive_terminal(self):
        env_patch = {k: v for k, v in os.environ.items() if k not in ("DNASTACK_NO_UPDATE_CHECK", "CI")}
        with patch.dict(os.environ, env_patch, clear=True), \
             patch("sys.stderr") as mock_stderr:
            mock_stderr.isatty.return_value = True
            assert _is_suppressed() is False


class TestCache:
    """Tests for cache read/write."""

    def test_write_and_read_cache(self, tmp_path):
        cache_file = tmp_path / UPDATE_CHECK_CACHE_FILENAME
        _write_cache(str(cache_file), "3.2.0")

        version, timestamp = _read_cache(str(cache_file))
        assert version == "3.2.0"
        assert timestamp is not None

    def test_read_missing_cache(self, tmp_path):
        cache_file = tmp_path / "nonexistent.json"
        version, timestamp = _read_cache(str(cache_file))
        assert version is None
        assert timestamp is None

    def test_read_corrupt_cache(self, tmp_path):
        cache_file = tmp_path / UPDATE_CHECK_CACHE_FILENAME
        cache_file.write_text("not json")
        version, timestamp = _read_cache(str(cache_file))
        assert version is None
        assert timestamp is None

    def test_cache_freshness(self, tmp_path):
        cache_file = tmp_path / UPDATE_CHECK_CACHE_FILENAME
        _write_cache(str(cache_file), "3.2.0")

        version, timestamp = _read_cache(str(cache_file))
        age_seconds = (datetime.now(timezone.utc) - timestamp).total_seconds()
        assert age_seconds < 5

    def test_write_cache_creates_parent_directory(self, tmp_path):
        cache_file = tmp_path / "subdir" / UPDATE_CHECK_CACHE_FILENAME
        _write_cache(str(cache_file), "3.2.0")

        version, _ = _read_cache(str(cache_file))
        assert version == "3.2.0"


class TestGetLatestStableVersion:
    """Tests for PyPI version fetching and filtering."""

    def test_returns_latest_stable_version(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "releases": {
                "3.0.0": [{}],
                "3.1.0": [{}],
                "3.2.0": [{}],
                "3.3.0a1": [{}],
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("requests.get", return_value=mock_response):
            version = _get_latest_stable_version()
            assert version == "3.2.0"

    def test_filters_out_prereleases(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "releases": {
                "3.0.0": [{}],
                "3.1.0a0": [{}],
                "3.1.0b1": [{}],
                "3.1.0rc1": [{}],
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("requests.get", return_value=mock_response):
            version = _get_latest_stable_version()
            assert version == "3.0.0"

    def test_skips_yanked_releases(self):
        """Releases with empty file lists are considered yanked/removed."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "releases": {
                "3.0.0": [{}],
                "3.1.0": [],
                "3.2.0": [{}],
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("requests.get", return_value=mock_response):
            version = _get_latest_stable_version()
            assert version == "3.2.0"

    def test_returns_none_on_network_error(self):
        with patch("requests.get", side_effect=Exception("Connection refused")):
            version = _get_latest_stable_version()
            assert version is None

    def test_returns_none_on_empty_releases(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"releases": {}}
        mock_response.raise_for_status = MagicMock()

        with patch("requests.get", return_value=mock_response):
            version = _get_latest_stable_version()
            assert version is None


class TestCheckForUpdate:
    """Tests for the main check_for_update function."""

    def test_update_available(self, tmp_path):
        with patch("dnastack.update_checker._get_latest_stable_version", return_value="3.2.0"), \
             patch("dnastack.update_checker.__version__", "3.1.0"), \
             patch("dnastack.update_checker._get_cache_path", return_value=str(tmp_path / UPDATE_CHECK_CACHE_FILENAME)):
            result = check_for_update(force=True)
            assert result.update_available is True
            assert result.latest_version == "3.2.0"
            assert result.check_failed is False

    def test_up_to_date(self, tmp_path):
        with patch("dnastack.update_checker._get_latest_stable_version", return_value="3.1.0"), \
             patch("dnastack.update_checker.__version__", "3.1.0"), \
             patch("dnastack.update_checker._get_cache_path", return_value=str(tmp_path / UPDATE_CHECK_CACHE_FILENAME)):
            result = check_for_update(force=True)
            assert result.update_available is False
            assert result.latest_version == "3.1.0"
            assert result.check_failed is False

    def test_network_failure(self, tmp_path):
        with patch("dnastack.update_checker._get_latest_stable_version", return_value=None), \
             patch("dnastack.update_checker._get_cache_path", return_value=str(tmp_path / UPDATE_CHECK_CACHE_FILENAME)):
            result = check_for_update(force=True)
            assert result.update_available is False
            assert result.latest_version is None
            assert result.check_failed is True

    def test_prerelease_user_not_notified_when_ahead(self, tmp_path):
        """User on 3.1.0a0 should NOT be notified about 3.0.5 (they're ahead)."""
        with patch("dnastack.update_checker._get_latest_stable_version", return_value="3.0.5"), \
             patch("dnastack.update_checker.__version__", "3.1.0a0"), \
             patch("dnastack.update_checker._get_cache_path", return_value=str(tmp_path / UPDATE_CHECK_CACHE_FILENAME)):
            result = check_for_update(force=True)
            assert result.update_available is False

    def test_prerelease_user_notified_when_stable_surpasses(self, tmp_path):
        """User on 3.1.0a0 SHOULD be notified about 3.1.0 (stable release of their alpha)."""
        with patch("dnastack.update_checker._get_latest_stable_version", return_value="3.1.0"), \
             patch("dnastack.update_checker.__version__", "3.1.0a0"), \
             patch("dnastack.update_checker._get_cache_path", return_value=str(tmp_path / UPDATE_CHECK_CACHE_FILENAME)):
            result = check_for_update(force=True)
            assert result.update_available is True
            assert result.latest_version == "3.1.0"

    def test_uses_fresh_cache_when_not_forced(self, tmp_path):
        cache_file = str(tmp_path / UPDATE_CHECK_CACHE_FILENAME)
        _write_cache(cache_file, "3.2.0")

        with patch("dnastack.update_checker.__version__", "3.1.0"), \
             patch("dnastack.update_checker._get_cache_path", return_value=cache_file), \
             patch("dnastack.update_checker._get_latest_stable_version") as mock_fetch:
            result = check_for_update(force=False)
            mock_fetch.assert_not_called()
            assert result.update_available is True
            assert result.latest_version == "3.2.0"

    def test_queries_pypi_when_cache_stale(self, tmp_path):
        cache_file = tmp_path / UPDATE_CHECK_CACHE_FILENAME
        cache_file.write_text(json.dumps({"latest_version": "3.1.0", "last_checked": "2020-01-01T00:00:00Z"}))

        with patch("dnastack.update_checker.__version__", "3.1.0"), \
             patch("dnastack.update_checker._get_cache_path", return_value=str(cache_file)), \
             patch("dnastack.update_checker._get_latest_stable_version", return_value="3.2.0"):
            result = check_for_update(force=False)
            assert result.update_available is True
            assert result.latest_version == "3.2.0"

    def test_force_bypasses_cache(self, tmp_path):
        cache_file = str(tmp_path / UPDATE_CHECK_CACHE_FILENAME)
        _write_cache(cache_file, "3.1.0")

        with patch("dnastack.update_checker.__version__", "3.1.0"), \
             patch("dnastack.update_checker._get_cache_path", return_value=cache_file), \
             patch("dnastack.update_checker._get_latest_stable_version", return_value="3.2.0"):
            result = check_for_update(force=True)
            assert result.update_available is True
            assert result.latest_version == "3.2.0"


class TestNotifyIfUpdateAvailable:
    """Tests for the stderr notification function."""

    def test_prints_notification_when_update_available(self, capsys):
        result = UpdateCheckResult(latest_version="3.2.0", update_available=True, check_failed=False)

        with patch("dnastack.update_checker.__version__", "3.1.0"), \
             patch("dnastack.update_checker._is_suppressed", return_value=False), \
             patch("dnastack.update_checker.check_for_update", return_value=result):
            notify_if_update_available()

        captured = capsys.readouterr()
        assert "3.2.0" in captured.err
        assert "pip install --upgrade dnastack-client-library" in captured.err
        assert captured.out == ""

    def test_silent_when_up_to_date(self, capsys):
        result = UpdateCheckResult(latest_version="3.1.0", update_available=False, check_failed=False)

        with patch("dnastack.update_checker._is_suppressed", return_value=False), \
             patch("dnastack.update_checker.check_for_update", return_value=result):
            notify_if_update_available()

        captured = capsys.readouterr()
        assert captured.err == ""
        assert captured.out == ""

    def test_silent_when_suppressed(self, capsys):
        with patch("dnastack.update_checker._is_suppressed", return_value=True):
            notify_if_update_available()

        captured = capsys.readouterr()
        assert captured.err == ""
        assert captured.out == ""

    def test_silent_when_check_fails(self, capsys):
        result = UpdateCheckResult(latest_version=None, update_available=False, check_failed=True)

        with patch("dnastack.update_checker._is_suppressed", return_value=False), \
             patch("dnastack.update_checker.check_for_update", return_value=result):
            notify_if_update_available()

        captured = capsys.readouterr()
        assert captured.err == ""
        assert captured.out == ""

    def test_silent_when_passive_suppressed_by_version_command(self, capsys):
        """Version command calls suppress_passive_notification() to avoid double notification."""
        result = UpdateCheckResult(latest_version="3.2.0", update_available=True, check_failed=False)

        suppress_passive_notification()

        with patch("dnastack.update_checker._is_suppressed", return_value=False), \
             patch("dnastack.update_checker.check_for_update", return_value=result):
            notify_if_update_available()

        captured = capsys.readouterr()
        assert captured.err == ""
        assert captured.out == ""

    def test_suppress_flag_resets_after_one_call(self, capsys):
        """The suppress flag should be one-shot — next call should notify normally."""
        result = UpdateCheckResult(latest_version="3.2.0", update_available=True, check_failed=False)

        suppress_passive_notification()

        with patch("dnastack.update_checker.__version__", "3.1.0"), \
             patch("dnastack.update_checker._is_suppressed", return_value=False), \
             patch("dnastack.update_checker.check_for_update", return_value=result):
            notify_if_update_available()  # Suppressed
            notify_if_update_available()  # Should fire

        captured = capsys.readouterr()
        assert "3.2.0" in captured.err
