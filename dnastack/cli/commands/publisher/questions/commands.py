from typing import Optional

from click import Group

from dnastack.cli.commands.publisher.questions.utils import (
    get_collection_service_client,
)
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import (
    ArgumentSpec,
    CONTEXT_ARG,
    SINGLE_ENDPOINT_ID_ARG,
    RESOURCE_OUTPUT_ARG,
)
from dnastack.cli.helpers.iterator_printer import show_iterator
from dnastack.common.logger import get_logger
from dnastack.common.tracing import Span

logger = get_logger(__name__)


def init_questions_commands(group: Group):
    @formatted_command(
        group=group,
        name='list',
        specs=[
            ArgumentSpec(
                name='collection',
                arg_names=['--collection', '-c'],
                help='Collection ID or slug name',
                required=True
            ),
            RESOURCE_OUTPUT_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def list_questions(collection: str, output: str, context: Optional[str], endpoint_id: Optional[str]):
        """List all questions for a collection"""
        trace = Span()
        client = get_collection_service_client(context=context, endpoint_id=endpoint_id)

        questions = client.list_questions(collection, trace=trace)

        show_iterator(
            output_format=output,
            iterator=questions,
            transform=lambda q: q.model_dump()
        )
