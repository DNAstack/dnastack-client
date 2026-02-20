from dnastack.cli.commands.workbench.namespaces.commands import init_namespace_commands
from dnastack.cli.commands.workbench.namespaces.members import members_command_group
from dnastack.cli.core.group import formatted_group


@formatted_group(name='namespaces')
def namespaces_commands():
    pass

# Initialize all commands
init_namespace_commands(namespaces_commands)

# Register sub-groups
namespaces_commands.add_command(members_command_group)
