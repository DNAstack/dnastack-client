from dnastack.cli.commands.auth.commands import init_auth_commands
from dnastack.cli.core.group import formatted_group


@formatted_group("auth")
def auth_command_group():
    """Manage authentication and authorization"""


# Initialize all commands
init_auth_commands(auth_command_group)

# Register sub-groups
