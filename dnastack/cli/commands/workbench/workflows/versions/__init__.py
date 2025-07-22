from dnastack.cli.commands.workbench.workflows.versions.commands import init_workflows_versions_commands
from dnastack.cli.commands.workbench.workflows.versions.defaults import workflows_versions_defaults_command_group
from dnastack.cli.commands.workbench.workflows.versions.transformations import \
    workflows_versions_transformations_command_group
from dnastack.cli.commands.workbench.workflows.versions.dependencies import dependencies
from dnastack.cli.core.group import formatted_group


@formatted_group('versions')
def workflows_versions_command_group():
    """ Create and interact with workflow versions """

# Initialize all commands
init_workflows_versions_commands(workflows_versions_command_group)

# Register sub-groups
workflows_versions_command_group.add_command(workflows_versions_defaults_command_group)
workflows_versions_command_group.add_command(workflows_versions_transformations_command_group)
workflows_versions_command_group.add_command(dependencies)
