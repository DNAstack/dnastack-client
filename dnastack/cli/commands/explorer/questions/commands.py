import csv
import json
import os
from typing import Optional

import click
from click import Group

from dnastack.cli.commands.explorer.questions.utils import (
    get_explorer_client,
    parse_collections_argument,
    validate_question_parameters,
    flatten_result_for_export
)
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import ArgumentSpec, CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG, ArgumentType, RESOURCE_OUTPUT_ARG, DATA_OUTPUT_ARG
from dnastack.cli.helpers.exporter import normalize
from dnastack.cli.helpers.iterator_printer import show_iterator
from dnastack.common.json_argument_parser import JsonLike, parse_and_merge_arguments
from dnastack.common.logger import get_logger
from dnastack.common.tracing import Span

logger = get_logger(__name__)


def init_questions_commands(group: Group):
    @formatted_command(
        group=group,
        name='list',
        specs=[
            RESOURCE_OUTPUT_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def list_questions(output: str, context: Optional[str], endpoint_id: Optional[str]):
        """List all available federated questions"""
        trace = Span()
        client = get_explorer_client(context=context, endpoint_id=endpoint_id, trace=trace)
        questions_iter = client.list_federated_questions(trace=trace)
        
        # Convert to list and pass to show_iterator
        questions = list(questions_iter)
        
        # For JSON/YAML output, show the raw question objects
        # No need for table formatting as show_iterator handles it
        show_iterator(
            output_format=output,
            iterator=questions,
            transform=lambda q: q.dict()
        )

    @formatted_command(
        group=group,
        name='describe',
        specs=[
            ArgumentSpec(
                name='question_id',
                arg_type=ArgumentType.POSITIONAL,
                help='The ID of the question to describe',
                required=True
            ),
            RESOURCE_OUTPUT_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def describe_question(question_id: str, output: str, context: Optional[str], endpoint_id: Optional[str]):
        """Get detailed information about a federated question"""
        trace = Span()
        client = get_explorer_client(context=context, endpoint_id=endpoint_id, trace=trace)
        question = client.describe_federated_question(question_id, trace=trace)
        
        # Use show_iterator for consistent output handling
        show_iterator(
            output_format=output,
            iterator=[question],  # Single item as list
            transform=lambda q: q.dict()
        )

    @formatted_command(
        group=group,
        name='ask',
        specs=[
            ArgumentSpec(
                name='question_name',
                arg_names=['--question-name'],
                help='The name/ID of the question to ask',
                required=True
            ),
            ArgumentSpec(
                name='args',
                arg_names=['--arg'],
                help='Question parameters in key=value format (can be used multiple times)',
                type=JsonLike,
                multiple=True
            ),
            ArgumentSpec(
                name='collections',
                arg_names=['--collections'],
                help='Comma-separated list of collection IDs to query (default: all collections for the question)'
            ),
            ArgumentSpec(
                name='output_file',
                arg_names=['--output-file'],
                help='Output file path for results'
            ),
            DATA_OUTPUT_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def ask_question(
        question_name: str,
        args: tuple,
        collections: Optional[str],
        output_file: Optional[str],
        output: str,
        context: Optional[str],
        endpoint_id: Optional[str]
    ):
        """Ask a federated question with the provided parameters"""
        trace = Span()
        client = get_explorer_client(context=context, endpoint_id=endpoint_id, trace=trace)
        
        # Parse collections if provided
        collection_ids = parse_collections_argument(collections)
        
        # Parse arguments
        inputs = {}
        if args:
            # When multiple=True with JsonLike, we get a tuple of JsonLike objects
            if isinstance(args, tuple):
                for arg in args:
                    parsed_args = arg.parsed_value() if hasattr(arg, 'parsed_value') else parse_and_merge_arguments(arg)
                    inputs.update(parsed_args)
            else:
                # Single JsonLike object
                parsed_args = args.parsed_value() if hasattr(args, 'parsed_value') else parse_and_merge_arguments(args)
                inputs.update(parsed_args)
        
        # Get question details for validation
        question = client.describe_federated_question(question_name, trace=trace)
        
        # Validate parameters
        try:
            inputs = validate_question_parameters(inputs, question)
        except ValueError as e:
            click.echo(f"Error: {e}", err=True)
            raise click.Abort()
        
        # If no collections specified, warn user about using all collections
        if collection_ids is None:
            collection_names = [col.name for col in question.collections]
            logger.info(f"No collections specified. Querying all {len(question.collections)} collections: {', '.join(collection_names)}")
        else:
            # Validate collection IDs exist in question
            available_ids = {col.id for col in question.collections}
            invalid_ids = [cid for cid in collection_ids if cid not in available_ids]
            if invalid_ids:
                click.echo(f"Warning: The following collection IDs are not available for this question: {', '.join(invalid_ids)}", err=True)
                collection_ids = [cid for cid in collection_ids if cid in available_ids]
                if not collection_ids:
                    click.echo("Error: No valid collection IDs provided", err=True)
                    raise click.Abort()
        
        # Execute the question
        results_iter = client.ask_federated_question(
            question_id=question_name,
            inputs=inputs,
            collections=collection_ids,
            trace=trace
        )
        
        # Collect results
        results = list(results_iter)
        
        if not results:
            click.echo("No results returned from query")
            return
        
        # Output results
        if output_file:
            _write_results_to_file(results, output_file, output)
            click.echo(f"Results written to {output_file}")
        else:
            # Use show_iterator for consistent output handling
            show_iterator(
                output_format=output,
                iterator=results
            )



def _write_results_to_file(results, output_file: str, output_format: str):
    """Write results to file"""
    # Ensure output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    if output_format == 'json':
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
    
    elif output_format == 'csv':
        # Flatten all results
        flattened_results = [flatten_result_for_export(result) for result in results]
        
        if not flattened_results:
            # Write empty file
            with open(output_file, 'w') as f:
                pass
            return
        
        # Get all possible column headers
        all_headers = set()
        for result in flattened_results:
            all_headers.update(result.keys())
        
        headers = sorted(all_headers)
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            
            for result in flattened_results:
                # Fill missing keys with empty strings
                row = {header: result.get(header, '') for header in headers}
                writer.writerow(row)
    
    elif output_format == 'yaml':
        # For YAML output, write as is
        with open(output_file, 'w') as f:
            normalized_results = [normalize(result) for result in results]
            from yaml import dump as to_yaml_string, SafeDumper
            yaml_content = to_yaml_string(normalized_results, Dumper=SafeDumper, sort_keys=False)
            f.write(yaml_content)