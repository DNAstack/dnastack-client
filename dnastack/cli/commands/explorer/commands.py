from dnastack.cli.commands.explorer.questions.commands import init_questions_commands
from dnastack.cli.core.group import formatted_group


@formatted_group("explorer")
def explorer_command_group():
    """Commands for working with Explorer federated questions"""
    pass


@formatted_group("questions")
def questions_command_group():
    """Commands for working with federated questions"""
    pass


# Initialize questions subcommands
init_questions_commands(questions_command_group)

# Register questions group under explorer
explorer_command_group.add_command(questions_command_group)