from dnastack.cli.commands.publisher.datasources.commands import init_datasources_commands
from dnastack.cli.core.group import formatted_group


@formatted_group("datasources")
def datasources_command_group():
    """Interact with data sources"""


# Initialize all commands
init_datasources_commands(datasources_command_group)
