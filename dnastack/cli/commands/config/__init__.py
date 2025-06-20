from dnastack.cli.commands.config.commands import init_config_commands
from dnastack.cli.commands.config.contexts import contexts_command_group
from dnastack.cli.commands.config.endpoints import endpoint_command_group
from dnastack.cli.commands.config.registries import registry_command_group
from dnastack.cli.core.group import formatted_group


@formatted_group("config")
def config_command_group():
    """Manage global configuration"""


# Initialize all commands
init_config_commands(config_command_group)

# Register sub-groups
config_command_group.add_command(registry_command_group)
config_command_group.add_command(endpoint_command_group)
config_command_group.add_command(contexts_command_group)
