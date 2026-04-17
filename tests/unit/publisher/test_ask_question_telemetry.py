from unittest.mock import MagicMock, patch

import click
from click.testing import CliRunner


def _build_cli(mock_client, metrics_enabled=True):
    """Build a test CLI with a mocked collection service client."""
    from dnastack.cli.commands.publisher.questions.commands import init_questions_commands

    @click.group()
    def cli():
        pass

    init_questions_commands(cli)
    return cli, mock_client


def _make_mock_client(raises=False):
    mock_client = MagicMock()
    mock_client.get_question.return_value = MagicMock(parameters=[])
    if raises:
        mock_client.ask_question.side_effect = RuntimeError("network failure")
    else:
        mock_client.ask_question.return_value = iter([{'col': 'val'}])
    return mock_client


class TestAskQuestionTelemetry:

    def _invoke(self, metrics_enabled=True, raises=False):
        mock_client = _make_mock_client(raises=raises)
        cli, _ = _build_cli(mock_client)

        with patch('dnastack.cli.commands.publisher.questions.commands.get_collection_service_client',
                   return_value=mock_client), \
             patch('dnastack.cli.commands.publisher.questions.commands.metrics_enabled', metrics_enabled), \
             patch('dnastack.cli.commands.publisher.questions.commands.handle_question_results_output'):
            runner = CliRunner()
            runner.invoke(cli, ['ask', '--question-name', 'q', '--collection', 'c'])

        return mock_client

    def test_submits_telemetry_on_success_when_enabled(self):
        client = self._invoke(metrics_enabled=True)
        client.submit_telemetry.assert_called_once()

    def test_does_not_submit_when_disabled(self):
        client = self._invoke(metrics_enabled=False)
        client.submit_telemetry.assert_not_called()

    def test_submits_with_success_outcome_on_success(self):
        client = self._invoke(metrics_enabled=True)
        payload = client.submit_telemetry.call_args[0][0]
        span = payload['resourceSpans'][0]['scopeSpans'][0]['spans'][0]
        outcome_attr = next(a for a in span['attributes'] if a['key'] == 'question.outcome')
        assert outcome_attr['value']['stringValue'] == 'success'

    def test_submits_with_error_outcome_on_failure(self):
        client = self._invoke(metrics_enabled=True, raises=True)
        client.submit_telemetry.assert_called_once()
        payload = client.submit_telemetry.call_args[0][0]
        span = payload['resourceSpans'][0]['scopeSpans'][0]['spans'][0]
        outcome_attr = next(a for a in span['attributes'] if a['key'] == 'question.outcome')
        assert outcome_attr['value']['stringValue'] == 'error'
