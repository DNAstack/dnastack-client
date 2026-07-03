from unittest.mock import MagicMock, patch

from dnastack.client.workbench.workbench_user_service.models import WorkbenchUser
from dnastack.client.workbench.workflow.client import GLOBAL_NAMESPACE


def test_workbench_user_allows_missing_default_namespace():
    # Platform admins have an account but no namespace, so default_namespace can be absent/null.
    assert WorkbenchUser(email="admin@example.com").default_namespace is None
    assert WorkbenchUser(email="admin@example.com", default_namespace=None).default_namespace is None
    assert WorkbenchUser(email="a@b.com", default_namespace="ns").default_namespace == "ns"


@patch("dnastack.cli.commands.workbench.workflows.utils.container")
@patch("dnastack.cli.commands.workbench.workflows.utils.get_user_client")
def test_get_workflow_client_global_uses_placeholder_and_skips_user_lookup(mock_get_user_client, mock_container):
    from dnastack.cli.commands.workbench.workflows.utils import get_workflow_client

    factory = MagicMock()
    mock_container.get.return_value = factory

    get_workflow_client(context_name="ctx", endpoint_id="ep", namespace=None, global_action=True)

    # A namespace-less platform admin must not trigger the users/me lookup that fails for them.
    mock_get_user_client.assert_not_called()
    assert factory.get.call_args.kwargs["namespace"] == GLOBAL_NAMESPACE


@patch("dnastack.cli.commands.workbench.workflows.utils.container")
@patch("dnastack.cli.commands.workbench.workflows.utils.get_user_client")
def test_get_workflow_client_non_global_resolves_default_namespace(mock_get_user_client, mock_container):
    from dnastack.cli.commands.workbench.workflows.utils import get_workflow_client

    factory = MagicMock()
    mock_container.get.return_value = factory
    user_client = MagicMock()
    user_client.get_user_config.return_value = WorkbenchUser(email="a@b.com", default_namespace="myns")
    mock_get_user_client.return_value = user_client

    get_workflow_client(context_name="ctx", endpoint_id="ep", namespace=None, global_action=False)

    mock_get_user_client.assert_called_once()
    assert factory.get.call_args.kwargs["namespace"] == "myns"


@patch("dnastack.cli.commands.workbench.workflows.utils.container")
@patch("dnastack.cli.commands.workbench.workflows.utils.get_user_client")
def test_get_workflow_client_explicit_namespace_wins_over_global(mock_get_user_client, mock_container):
    from dnastack.cli.commands.workbench.workflows.utils import get_workflow_client

    factory = MagicMock()
    mock_container.get.return_value = factory

    get_workflow_client(context_name="ctx", endpoint_id="ep", namespace="explicit", global_action=True)

    mock_get_user_client.assert_not_called()
    assert factory.get.call_args.kwargs["namespace"] == "explicit"
