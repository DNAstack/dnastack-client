"""Unit tests for rendering an engine health check failure."""
from unittest.mock import Mock

import click
import pytest

from dnastack.cli.commands.workbench.engines.health_check_failure import (
    exit_on_failed_health_check, health_check_report,
)
from dnastack.client.workbench.ewes.models import Check
from dnastack.http.session import ClientError

BODY = {
    'msg': 'Initial engine health check failed.', 'error_code': 400, 'trace_id': 'trace-123',
    'errors': [{'checks': [
        {'type': 'CONNECTIVITY', 'outcome': 'SUCCESS'},
        {'type': 'CREDENTIALS', 'outcome': 'FAILURE', 'error': "Permission 'run.services.get' denied"},
    ]}],
}


def _error(status=400, body=BODY, json_error=None):
    response = Mock(status_code=status, text='raw')
    response.json = Mock(side_effect=json_error) if json_error else Mock(return_value=body)
    return ClientError(response)


def test_report_lists_every_check_with_its_outcome():
    checks = [Check(**c) for c in BODY['errors'][0]['checks']]
    report = click.unstyle(health_check_report('giab-demo', 'created', checks, 'trace-123'))
    assert report.splitlines() == [
        "Engine 'giab-demo' failed its health check and was not created.",
        '',
        '  ✓ SUCCESS  CONNECTIVITY',
        "  ✗ FAILURE  CREDENTIALS   Permission 'run.services.get' denied",
        '',
        'Fix the engine description and run the command again.',
        'Incident ID trace-123',
    ]


def test_failures_are_red():
    checks = [Check(**c) for c in BODY['errors'][0]['checks']]
    report = health_check_report('e', 'updated', checks, None)
    assert click.style("  ✗ FAILURE  CREDENTIALS   Permission 'run.services.get' denied", fg='red') in report
    assert 'Incident ID' not in report


def test_exits_with_report(capsys):
    with pytest.raises(SystemExit) as exit_info:
        exit_on_failed_health_check(_error(), 'giab-demo', 'created')
    assert exit_info.value.code == 1
    assert 'failed its health check and was not created' in capsys.readouterr().err


@pytest.mark.parametrize('error', [
    _error(status=403),
    _error(body={'msg': 'Engine ID must be unique.', 'error_code': 400}),
    _error(body={'errors': ['not a dict']}),
    _error(body={'errors': [{'checks': [{'type': 'NOT_A_CHECK', 'outcome': 'FAILURE'}]}]}),
    _error(json_error=ValueError('not JSON')),
])
def test_other_errors_fall_through(error):
    assert exit_on_failed_health_check(error, 'e', 'created') is None


def test_report_masks_the_given_secrets_in_check_errors():
    checks = [Check(type='CREDENTIALS', outcome='FAILURE', error='key SECRET-X refused')]
    report = click.unstyle(health_check_report('e', 'created', checks, None, secrets=['SECRET-X']))
    assert 'key *** refused' in report
    assert 'SECRET-X' not in report
