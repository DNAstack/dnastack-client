from dnastack.cli.commands.workbench.storage.add import add_storage_command_group
from dnastack.cli.commands.workbench.storage.commands import init_storage_commands
from dnastack.cli.commands.workbench.storage.update import update_storage_command_group
from dnastack.cli.core.group import formatted_group


@formatted_group("storage")
def storage_command_group():
    """Interact with Storage accounts"""


# Initialize all commands
init_storage_commands(storage_command_group)

# Register sub-groups
storage_command_group.add_command(add_storage_command_group)
storage_command_group.add_command(update_storage_command_group)
