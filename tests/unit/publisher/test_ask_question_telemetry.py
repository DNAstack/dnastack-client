from unittest.mock import MagicMock, patch

import click
from click.testing import CliRunner


def _build_cli():
    from dnastack.cli.commands.publisher.questions.commands import init_questions_commands

    @click.group()
    def cli():
        pass

    init_questions_commands(cli)
    return cli


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
        cli = _build_cli()

        with patch('dnastack.cli.commands.publisher.questions.commands.get_collection_service_client',
                   return_value=mock_client), \
             patch('dnastack.cli.commands.publisher.questions.commands.metrics_enabled', metrics_enabled), \
             patch('dnastack.cli.commands.publisher.questions.commands.handle_question_results_output'), \
             patch('dnastack.cli.commands.publisher.questions.commands.submit_telemetry') as mock_submit:
            runner = CliRunner()
            runner.invoke(cli, ['ask', '--question-name', 'q', '--collection', 'c'])

        return mock_client, mock_submit

    def test_submits_telemetry_on_success_when_enabled(self):
        _, mock_submit = self._invoke(metrics_enabled=True)
        mock_submit.assert_called_once()

    def test_does_not_submit_when_disabled(self):
        _, mock_submit = self._invoke(metrics_enabled=False)
        mock_submit.assert_not_called()

    def test_submits_with_success_outcome_on_success(self):
        _, mock_submit = self._invoke(metrics_enabled=True)
        args, kwargs = mock_submit.call_args
        # submit_telemetry(client, question_name, collection, start_ns, end_ns, outcome)
        outcome = args[5]
        assert outcome == 'success'

    def test_submits_with_error_outcome_on_failure(self):
        _, mock_submit = self._invoke(metrics_enabled=True, raises=True)
        mock_submit.assert_called_once()
        args, kwargs = mock_submit.call_args
        outcome = args[5]
        assert outcome == 'error'

    def test_question_name_and_collection_passed_to_telemetry(self):
        _, mock_submit = self._invoke(metrics_enabled=True)
        args, kwargs = mock_submit.call_args
        # submit_telemetry(client, question_name, collection, start_ns, end_ns, outcome)
        assert args[1] == 'q'
        assert args[2] == 'c'

    def test_original_exception_propagates(self):
        """Telemetry submission in finally must not swallow the original exception."""
        mock_client = _make_mock_client(raises=True)
        cli = _build_cli()

        with patch('dnastack.cli.commands.publisher.questions.commands.get_collection_service_client',
                   return_value=mock_client), \
             patch('dnastack.cli.commands.publisher.questions.commands.metrics_enabled', True), \
             patch('dnastack.cli.commands.publisher.questions.commands.submit_telemetry'), \
             patch('dnastack.cli.commands.publisher.questions.commands.handle_question_results_output'):
            runner = CliRunner()
            result = runner.invoke(cli, ['ask', '--question-name', 'q', '--collection', 'c'])

        # CliRunner catches exceptions — verify the exception was raised (exit code != 0)
        assert result.exit_code != 0
