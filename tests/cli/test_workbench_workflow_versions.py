"""`workbench workflows versions create --global` drives the global/admin path (admin_only_action);
the resulting X-Global-Namespace header is asserted at the client layer in
tests/unit/client/workbench/workflow/test_workflow_client_admin_header.py."""
from unittest import TestCase
from unittest.mock import Mock, patch

from click.testing import CliRunner

from dnastack.cli.commands.workbench.workflows.versions import workflows_versions_command_group
from dnastack.client.workbench.workflow.models import WorkflowVersion

_GET_CLIENT = 'dnastack.cli.commands.workbench.workflows.versions.commands.get_workflow_client'
_EMPTY_ZIP = b'PK\x05\x06' + b'\x00' * 18


class TestWorkflowVersionCreateGlobalFlag(TestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.mock_workflow_client = Mock()
        self.mock_workflow_client.create_version.return_value = WorkflowVersion(
            id='v-id',
            versionName='2.0',
            workflowName='test-workflow',
            descriptorType='WDL',
        )

    def _invoke_create(self, *extra_args):
        with self.runner.isolated_filesystem():
            with open('compress_wdl_files.zip', 'wb') as zip_file:
                zip_file.write(_EMPTY_ZIP)
            return self.runner.invoke(workflows_versions_command_group, [
                'create',
                '--workflow', 'workflow-1',
                '--name', '2.0',
                '--entrypoint', 'main.wdl',
                *extra_args,
                'compress_wdl_files.zip',
            ])

    @patch(_GET_CLIENT)
    def test_create_version_with_global_flag_is_admin_only_action(self, mock_get_client):
        mock_get_client.return_value = self.mock_workflow_client

        result = self._invoke_create('--global')

        self.assertEqual(result.exit_code, 0, msg=f"{result.output}\n{result.exception}")
        self.mock_workflow_client.create_version.assert_called_once()
        self.assertTrue(self.mock_workflow_client.create_version.call_args.kwargs['admin_only_action'])

    @patch(_GET_CLIENT)
    def test_create_version_without_global_flag_is_not_admin_only_action(self, mock_get_client):
        mock_get_client.return_value = self.mock_workflow_client

        result = self._invoke_create()

        self.assertEqual(result.exit_code, 0, msg=f"{result.output}\n{result.exception}")
        self.mock_workflow_client.create_version.assert_called_once()
        self.assertFalse(self.mock_workflow_client.create_version.call_args.kwargs['admin_only_action'])
