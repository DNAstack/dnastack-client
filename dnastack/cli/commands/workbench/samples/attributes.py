import json
from pathlib import Path
from typing import Optional

import click

from dnastack.cli.commands.workbench.utils import get_samples_client, NAMESPACE_ARG
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import ArgumentSpec, ArgumentType, CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG
from dnastack.cli.core.group import formatted_group
from dnastack.common.json_argument_parser import FileOrValue

BULK_SUFFIX = '.attributes.json'


@formatted_group("attributes")
def attributes_command_group():
    """ Read and write a sample's custom attributes """


SAMPLE_ID_ARG = ArgumentSpec(
    name='sample_id',
    arg_type=ArgumentType.POSITIONAL,
    help='The ID of the sample.',
    required=True,
)


def _fail(message: str):
    # SystemExit is a BaseException, so it carries this message out past formatted_command's
    # blanket handler, which would otherwise prefix it with the exception class name.
    click.secho(message, fg='red', err=True)
    raise SystemExit(1)


def _document_from(attributes: FileOrValue) -> str:
    raw = attributes.raw_value
    named = raw.lstrip('@')
    if named.lower().endswith(BULK_SUFFIX):
        _fail(f'{named} looks like a bulk attributes document, which is keyed by sample ID.\n'
              f'Use "samples metadata upload" to apply one, or pass this sample\'s attributes '
              f'on their own as @FILE, - or a JSON literal.')

    document = attributes.value()
    try:
        parsed = json.loads(document)
    except (TypeError, ValueError):
        hint = f'\nDid you mean @{named}?' if Path(named).is_file() else ''
        _fail(f'Attributes must be a JSON object.{hint}')
    else:
        if not isinstance(parsed, dict):
            _fail('Attributes must be a JSON object.')
    return document


@formatted_command(
    group=attributes_command_group,
    name='get',
    specs=[SAMPLE_ID_ARG, NAMESPACE_ARG, CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG]
)
def get_attributes(context: Optional[str],
                   endpoint_id: Optional[str],
                   namespace: Optional[str],
                   sample_id: str):
    """
    Print a sample's custom attributes, exactly as stored.

    Prints {} when the sample has none.

    docs: https://docs.omics.ai/products/command-line-interface/reference/workbench/samples-attributes-get
    """
    client = get_samples_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
    # Echoed unparsed: the shared printer sorts keys and hoists `id`, which would rewrite the document.
    click.echo(client.get_sample_attributes(sample_id))


@formatted_command(
    group=attributes_command_group,
    name='set',
    specs=[
        SAMPLE_ID_ARG,
        ArgumentSpec(
            name='attributes',
            arg_type=ArgumentType.POSITIONAL,
            help='The attributes to store, as @FILE, - to read stdin, or a JSON literal.',
            required=True,
            type=FileOrValue,
        ),
        NAMESPACE_ARG,
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ]
)
def set_attributes(context: Optional[str],
                   endpoint_id: Optional[str],
                   namespace: Optional[str],
                   sample_id: str,
                   attributes: FileOrValue):
    """
    Replace a sample's custom attributes.

    Takes the attributes on their own, as a JSON object:

      dnastack workbench samples attributes set HG002 '{"kit_lot": "A7-2291"}'
      dnastack workbench samples attributes set HG002 @bag.json
      cat bag.json | dnastack workbench samples attributes set HG002 -

    This replaces the whole set. Attributes the document omits are deleted, so include everything
    you want to keep. There is no per-key update.

    To set attributes on many samples at once, use "samples metadata upload" with a file named
    *.attributes.json, whose document is keyed by sample ID.

    docs: https://docs.omics.ai/products/command-line-interface/reference/workbench/samples-attributes-set
    """
    document = _document_from(attributes)
    client = get_samples_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
    click.echo(client.replace_sample_attributes(sample_id, document))


@formatted_command(
    group=attributes_command_group,
    name='clear',
    specs=[
        SAMPLE_ID_ARG,
        ArgumentSpec(
            name='force',
            arg_names=['--force', '-f'],
            help='Do not prompt for confirmation.',
            type=bool,
            default=False,
        ),
        NAMESPACE_ARG,
        CONTEXT_ARG,
        SINGLE_ENDPOINT_ID_ARG,
    ]
)
def clear_attributes(context: Optional[str],
                     endpoint_id: Optional[str],
                     namespace: Optional[str],
                     sample_id: str,
                     force: bool = False):
    """
    Remove all of a sample's custom attributes.

    This cannot be undone. Pedigree and phenotypes are separate and are left alone.

    docs: https://docs.omics.ai/products/command-line-interface/reference/workbench/samples-attributes-clear
    """
    if not force and not click.confirm(f'Do you want to remove every custom attribute from "{sample_id}"?'):
        return
    client = get_samples_client(context_name=context, endpoint_id=endpoint_id, namespace=namespace)
    click.echo(client.replace_sample_attributes(sample_id, '{}'))
