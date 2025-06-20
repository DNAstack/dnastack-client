from dnastack.cli.commands.workbench.workflows.commands import init_workflows_commands
from dnastack.cli.commands.workbench.workflows.versions import workflows_versions_command_group
from dnastack.cli.core.group import formatted_group


@formatted_group("workflows")
def workflows_command_group():
    """Create and interact with workflows"""


# Initialize all commands
init_workflows_commands(workflows_command_group)

# Register sub-groups
workflows_command_group.add_command(workflows_versions_command_group)
