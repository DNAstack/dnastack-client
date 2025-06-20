from dnastack.cli.commands.drs.commands import init_drs_commands
from dnastack.cli.core.group import formatted_group


@formatted_group("files", aliases=["drs"])
def drs_command_group():
    """Interact with Data Repository Service"""


# Initialize all commands
init_drs_commands(drs_command_group)

# Register sub-groups
