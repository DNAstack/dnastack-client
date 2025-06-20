from dnastack.cli.commands.publisher.collections.commands import init_collections_commands
from dnastack.cli.commands.publisher.collections.items import items_command_group
from dnastack.cli.commands.publisher.collections.tables import tables_command_group
from dnastack.cli.core.group import formatted_group


@formatted_group("collections")
def collections_command_group():
    """Interact with collections"""


# Initialize all commands
init_collections_commands(collections_command_group)

# Register sub-groups
collections_command_group.add_command(items_command_group)
collections_command_group.add_command(tables_command_group)
