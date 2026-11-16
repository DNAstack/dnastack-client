from dnastack.cli.commands.publisher.tenants.commands import init_tenants_commands
from dnastack.cli.core.group import formatted_group


@formatted_group('tenants')
def tenants_command_group():
    """ Manage Publisher tenants """


init_tenants_commands(tenants_command_group)
