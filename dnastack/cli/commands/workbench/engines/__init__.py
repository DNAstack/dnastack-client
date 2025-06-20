from dnastack.cli.commands.workbench.engines.commands import init_engines_commands
from dnastack.cli.commands.workbench.engines.healthchecks import engine_healthchecks_command_group
from dnastack.cli.commands.workbench.engines.parameters import engine_parameters_command_group
from dnastack.cli.core.group import formatted_group


@formatted_group("engines")
def engines_command_group():
    """Interact with engines"""


# Initialize all commands
init_engines_commands(engines_command_group)

# Register sub-groups
engines_command_group.add_command(engine_parameters_command_group)
engines_command_group.add_command(engine_healthchecks_command_group)
