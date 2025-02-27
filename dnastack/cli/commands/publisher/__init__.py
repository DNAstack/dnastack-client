from dnastack.cli.commands.publisher.collections import collections_command_group
from dnastack.cli.commands.publisher.datasources import datasources_command_group
from dnastack.cli.core.group import formatted_group


@formatted_group('publisher')
def publisher_command_group():
    """ Interact with Publisher """


publisher_command_group.add_command(collections_command_group)
publisher_command_group.add_command(datasources_command_group)
