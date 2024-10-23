import click

from dnastack.cli.workbench.instruments_commands import instruments_command_group
from dnastack.cli.workbench.namespace_commands import namespace_commands
from dnastack.cli.workbench.runs_commands import runs_command_group
from dnastack.cli.workbench.workflows_commands import workflows_command_group
from dnastack.cli.workbench.engines_commands import engines_command_group
from dnastack.cli.workbench.samples_commands import samples_command_group
from dnastack.cli.workbench.storage_commands import storage_command_group


@click.group('workbench')
def workbench_command_group():
    """ Interact with Workbench """


workbench_command_group.add_command(runs_command_group)
workbench_command_group.add_command(workflows_command_group)
workbench_command_group.add_command(engines_command_group)
workbench_command_group.add_command(namespace_commands)
workbench_command_group.add_command(samples_command_group)
workbench_command_group.add_command(storage_command_group)
workbench_command_group.add_command(instruments_command_group)

