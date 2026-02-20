from dnastack.cli.commands.workbench.namespaces.members.commands import init_members_commands
from dnastack.cli.core.group import formatted_group


@formatted_group('members')
def members_command_group():
    """Interact with namespace members"""

# Initialize all commands
init_members_commands(members_command_group)
