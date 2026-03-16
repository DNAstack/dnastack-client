from dnastack.cli.commands.publisher.questions.commands import init_questions_commands
from dnastack.cli.core.group import formatted_group


@formatted_group('questions')
def questions_command_group():
    """Interact with collection questions"""


init_questions_commands(questions_command_group)
