from dnastack.cli.commands.workbench.namespaces.commands import init_namespace_commands
from dnastack.cli.core.group import formatted_group


@formatted_group(name="namespaces")
def namespaces_commands():
    pass


# Initialize all commands
init_namespace_commands(namespaces_commands)

# Register sub-groups
