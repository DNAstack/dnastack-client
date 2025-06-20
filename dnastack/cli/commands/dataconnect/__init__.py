from dnastack.cli.commands.dataconnect.commands import init_data_connect_commands
from dnastack.cli.commands.dataconnect.tables import tables_command_group
from dnastack.cli.core.group import formatted_group


@formatted_group("data-connect", aliases=["dataconnect", "dc"])
def data_connect_command_group():
    """Interact with Data Connect Service"""


# Initialize all commands
init_data_connect_commands(data_connect_command_group)

# Register sub-groups
data_connect_command_group.add_command(tables_command_group)
