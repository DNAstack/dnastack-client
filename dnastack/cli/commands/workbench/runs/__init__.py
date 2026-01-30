from dnastack.cli.commands.workbench.runs.commands import init_runs_commands
from dnastack.cli.commands.workbench.runs.events import events_command_group
from dnastack.cli.commands.workbench.runs.hooks import hooks_command_group
from dnastack.cli.commands.workbench.runs.tasks import tasks_command_group
from dnastack.cli.core.group import formatted_group


@formatted_group('runs')
def runs_command_group():
    """Submit workflows for execution or interact with existing runs"""

# Initialize all commands
init_runs_commands(runs_command_group)

# Register sub-groups
runs_command_group.add_command(tasks_command_group)
runs_command_group.add_command(events_command_group)
runs_command_group.add_command(hooks_command_group)
