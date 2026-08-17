from dnastack.cli.commands.workbench.samples.attributes import attributes_command_group
from dnastack.cli.commands.workbench.samples.commands import init_samples_commands
from dnastack.cli.commands.workbench.samples.files import files_command_group
from dnastack.cli.commands.workbench.samples.metadata import metadata_command_group
from dnastack.cli.core.group import formatted_group


@formatted_group('samples')
def samples_command_group():
    """ Interact with samples """

# Initialize all commands
init_samples_commands(samples_command_group)

# Register sub-groups
samples_command_group.add_command(files_command_group)
samples_command_group.add_command(metadata_command_group)
samples_command_group.add_command(attributes_command_group)
