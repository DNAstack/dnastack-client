from dnastack.cli.commands.collections.commands import init_collections_commands
from dnastack.cli.commands.collections.tables import tables_command_group
from dnastack.cli.core.group import formatted_group


@formatted_group("collections", aliases=["cs"])
def collections_command_group():
    """Interact with Collection Service or Explorer Service (e.g., Viral AI)"""


# Initialize all commands
init_collections_commands(collections_command_group)

# Register sub-groups
collections_command_group.add_command(tables_command_group)
