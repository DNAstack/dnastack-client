from dnastack.cli.commands.workbench.engines import engines_command_group
from dnastack.cli.commands.workbench.instruments import instruments_command_group
from dnastack.cli.commands.workbench.namespaces import namespaces_commands
from dnastack.cli.commands.workbench.runs import runs_command_group
from dnastack.cli.commands.workbench.samples import samples_command_group
from dnastack.cli.commands.workbench.storage import storage_command_group
from dnastack.cli.commands.workbench.workflows import workflows_command_group
from dnastack.cli.core.group import formatted_group


@formatted_group("workbench")
def workbench_command_group():
    """Interact with Workbench"""


workbench_command_group.add_command(runs_command_group)
workbench_command_group.add_command(workflows_command_group)
workbench_command_group.add_command(engines_command_group)
workbench_command_group.add_command(namespaces_commands)
workbench_command_group.add_command(samples_command_group)
workbench_command_group.add_command(storage_command_group)
workbench_command_group.add_command(instruments_command_group)
