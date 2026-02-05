from dnastack.cli.commands.workbench.runs.samples.commands import init_samples_commands
from dnastack.cli.core.group import formatted_group


@formatted_group('samples')
def samples_command_group():
    """Manage the samples associated with a run"""


init_samples_commands(samples_command_group)
