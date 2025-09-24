import csv
import json
import os
from typing import Optional, Dict, Any, List

import click
from imagination import container

from dnastack.client.explorer.client import ExplorerClient
from dnastack.cli.helpers.client_factory import ConfigurationBasedClientFactory
from dnastack.cli.helpers.exporter import normalize
from dnastack.cli.helpers.iterator_printer import show_iterator
from dnastack.common.tracing import Span


def get_explorer_client(context: Optional[str] = None, 
                       endpoint_id: Optional[str] = None,
                       trace: Optional[Span] = None) -> ExplorerClient:
    """
    Get an Explorer client instance.
    
    Args:
        context: Optional context name
        endpoint_id: Optional endpoint ID
        trace: Optional tracing span
        
    Returns:
        ExplorerClient: Configured explorer client
    """
    factory: ConfigurationBasedClientFactory = container.get(ConfigurationBasedClientFactory)
    return factory.get(ExplorerClient, context_name=context, endpoint_id=endpoint_id)


def parse_collections_argument(collections_str: Optional[str]) -> Optional[List[str]]:
    """
    Parse a collections string into a list.
    Handles both comma-separated and newline-separated formats.

    Args:
        collections_str: Collection IDs as either:
                        - Comma-separated (e.g., "id1,id2,id3")
                        - Newline-separated (one ID per line)

    Returns:
        List[str] or None: List of collection IDs or None if input is None/empty
    """
    if not collections_str:
        return None

    # Check if it contains newlines (multiline file format)
    if '\n' in collections_str:
        # Split by newlines and strip whitespace
        collections = [col.strip() for col in collections_str.split('\n')]
    else:
        # Split by comma and strip whitespace
        collections = [col.strip() for col in collections_str.split(',')]

    # Filter out empty strings
    return [col for col in collections if col]


def format_question_parameters(params) -> str:
    """
    Format question parameters for display.
    
    Args:
        params: List of QuestionParam objects
        
    Returns:
        str: Formatted parameter description
    """
    if not params:
        return "No parameters"
    
    lines = []
    for param in params:
        required_marker = " (required)" if param.required else " (optional)"
        param_line = f"  {param.name}: {param.input_type}{required_marker}"
        
        if param.description:
            param_line += f" - {param.description}"
            
        if param.default_value:
            param_line += f" [default: {param.default_value}]"
            
        # Handle dropdown values
        if param.values and param.input_subtype == "DROPDOWN":
            values_list = param.values.split('\n')
            if values_list:
                param_line += f" [choices: {', '.join(values_list[:5])}{'...' if len(values_list) > 5 else ''}]"
        
        lines.append(param_line)
    
    return "\n".join(lines)


def format_question_collections(collections) -> str:
    """
    Format question collections for display.
    
    Args:
        collections: List of QuestionCollection objects
        
    Returns:
        str: Formatted collections description
    """
    if not collections:
        return "No collections"
    
    lines = []
    for col in collections:
        lines.append(f"  {col.name} ({col.slug}) - ID: {col.id}")
    
    return "\n".join(lines)


def validate_question_parameters(inputs: Dict[str, str], question) -> Dict[str, str]:
    """
    Basic validation of question parameters.
    
    Args:
        inputs: Dictionary of parameter values
        question: FederatedQuestion object with parameter definitions
        
    Returns:
        Dict[str, str]: Validated inputs
        
    Raises:
        ValueError: If required parameters are missing
    """
    # Check for required parameters
    required_params = [p.name for p in question.params if p.required]
    missing_params = [p for p in required_params if p not in inputs]
    
    if missing_params:
        raise ValueError(f"Missing required parameters: {', '.join(missing_params)}")
    
    return inputs


def flatten_result_for_export(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Flatten a nested result dictionary for CSV/TSV export.
    
    Args:
        result: Nested dictionary result
        
    Returns:
        Dict[str, Any]: Flattened dictionary
    """
    flattened = {}
    
    def _flatten(obj, prefix=''):
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_key = f"{prefix}.{key}" if prefix else key
                _flatten(value, new_key)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                new_key = f"{prefix}[{i}]" if prefix else f"item_{i}"
                _flatten(item, new_key)
        else:
            flattened[prefix] = obj
    
    _flatten(result)
    return flattened


def handle_question_results_output(results: List[Dict[str, Any]], output_file: Optional[str], output_format: str):
    """
    Handle output of question results to file or stdout.
    
    Args:
        results: List of result dictionaries
        output_file: Optional file path to write to
        output_format: Output format (json, csv, yaml, etc.)
    """
    if output_file:
        write_results_to_file(results, output_file, output_format)
        click.echo(f"Results written to {output_file}")
    else:
        # Use show_iterator for consistent output handling
        show_iterator(
            output_format=output_format,
            iterator=results
        )


def write_results_to_file(results: List[Dict[str, Any]], output_file: str, output_format: str):
    """
    Write results to file in the specified format.
    
    Args:
        results: List of result dictionaries
        output_file: File path to write to
        output_format: Output format (json, csv, yaml)
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    if output_format == 'json':
        _write_json_results(results, output_file)
    elif output_format == 'csv':
        _write_csv_results(results, output_file)
    elif output_format == 'yaml':
        _write_yaml_results(results, output_file)


def _write_json_results(results: List[Dict[str, Any]], output_file: str):
    """Write results as JSON."""
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)


def _write_csv_results(results: List[Dict[str, Any]], output_file: str):
    """Write results as CSV with flattened structure."""
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


def _write_yaml_results(results: List[Dict[str, Any]], output_file: str):
    """Write results as YAML."""
    with open(output_file, 'w') as f:
        normalized_results = [normalize(result) for result in results]
        from yaml import dump as to_yaml_string, SafeDumper
        yaml_content = to_yaml_string(normalized_results, Dumper=SafeDumper, sort_keys=False)
        f.write(yaml_content)