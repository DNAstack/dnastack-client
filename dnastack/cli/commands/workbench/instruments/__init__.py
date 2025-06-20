from dnastack.cli.commands.workbench.instruments.commands import init_instruments_commands
from dnastack.cli.core.group import formatted_group


@formatted_group("instruments")
def instruments_command_group():
    """Interact with instruments"""


# Initialize all commands
init_instruments_commands(instruments_command_group)

# Register sub-groups
