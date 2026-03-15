from typing import Optional, Dict, Any, List

from imagination import container

from dnastack.client.collections.client import CollectionServiceClient
from dnastack.cli.helpers.client_factory import ConfigurationBasedClientFactory


def get_collection_service_client(
    context: Optional[str] = None,
    endpoint_id: Optional[str] = None
) -> CollectionServiceClient:
    """
    Get a CollectionServiceClient instance.

    Args:
        context: Optional context name
        endpoint_id: Optional endpoint ID

    Returns:
        CollectionServiceClient: Configured client
    """
    factory: ConfigurationBasedClientFactory = container.get(ConfigurationBasedClientFactory)
    return factory.get(
        CollectionServiceClient,
        context_name=context,
        endpoint_id=endpoint_id
    )


def validate_question_parameters(inputs: Dict[str, str], question) -> Dict[str, str]:
    """
    Validate question parameters against question schema.

    Args:
        inputs: User-provided parameters
        question: Question object with parameter definitions

    Returns:
        Dict[str, str]: Validated parameters

    Raises:
        ValueError: If required parameters are missing
    """
    required_params = [p.name for p in question.parameters if p.required]
    missing_params = [p for p in required_params if p not in inputs]

    if missing_params:
        raise ValueError(f"Missing required parameters: {', '.join(missing_params)}")

    return inputs


def handle_question_results_output(
    results: List[Dict[str, Any]],
    output_file: Optional[str],
    output_format: str
):
    """
    Handle output of question results to file or stdout.
    Reuses logic from explorer questions utils.

    Args:
        results: List of result dictionaries
        output_file: Optional file path to write to
        output_format: Output format (json, csv, yaml, table)
    """
    # Import from explorer utils to reuse existing implementation
    from dnastack.cli.commands.explorer.questions.utils import (
        handle_question_results_output as explorer_output_handler
    )

    explorer_output_handler(results, output_file, output_format)
