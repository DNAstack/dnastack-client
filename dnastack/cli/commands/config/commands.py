import json

import click
from click import Group
from imagination import container

from dnastack.cli.core.command import formatted_command
from dnastack.configuration.manager import ConfigurationManager
from dnastack.configuration.models import Configuration


def init_config_commands(group: Group):
    @formatted_command(
        group=group,
        name='schema',
        specs=[]
    )
    def config_schema():
        """Show the schema of the configuration file"""
        click.echo(json.dumps(Configuration.model_json_schema(), indent=2, sort_keys=True))


    @formatted_command(
        group=group,
        name='reset',
        specs=[]
    )
    def reset():
        """Reset the configuration file"""
        manager: ConfigurationManager = container.get(ConfigurationManager)
        manager.hard_reset()
