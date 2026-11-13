from dnastack.cli.commands.workbench.users.commands import init_users_commands
from dnastack.cli.core.group import formatted_group


@formatted_group('users')
def users_command_group():
    """Interact with Workbench users"""

# Initialize all commands
init_users_commands(users_command_group)
