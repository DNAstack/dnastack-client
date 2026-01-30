from dnastack.cli.commands.workbench.runs.hooks.commands import init_hooks_commands
from dnastack.cli.core.group import formatted_group


@formatted_group('hooks')
def hooks_command_group():
    """Interact with a run's hooks"""

# Initialize all commands
init_hooks_commands(hooks_command_group)