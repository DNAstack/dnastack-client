import click
from click import Command, Option, Parameter, Argument
from typing import List

from dnastack.cli.core.constants import APP_NAME, INDENT, OPTION_WIDTH, OPTION_PADDING, TOTAL_WIDTH
from dnastack.cli.core.formatting_utils import get_visual_length, wrap_text
from dnastack.cli.core.styling import styler

class FormattedHelpCommand(Command):
    """Command class that provides formatted and colored help output."""
    def __init__(self, *args, **kwargs):
        kwargs['context_settings'] = {
            'help_option_names': ['-h', '--help'],  # Add all help variants
            'token_normalize_func': lambda x: x.lower(),    # Make help flags case-insensitive
        }
        super().__init__(*args, **kwargs)
        # Store help texts for arguments
        self.argument_help_texts = {}

    def store_argument_help(self, arg_name: str, help_text: str):
        """Store help text for an argument"""
        self.argument_help_texts[arg_name] = help_text

    def get_help(self, ctx: click.Context) -> str:
        """Override get_help to customize and colorize the help output."""
        # Extract the command description
        description = self.help or ''

        # Organize parameters
        positional_args: List[Parameter] = []
        required_options: List[Parameter] = []
        optional_options: List[Parameter] = []

        for param in self.params:
            if isinstance(param, Argument):
                positional_args.append(param)
            elif isinstance(param, Option):
                if param.required:
                    required_options.append(param)
                else:
                    optional_options.append(param)

        # Build the command path without the full executable path
        ctx_path_parts = ctx.command_path.split()
        if ctx_path_parts[0].endswith('__main__.py'):
            command_parts = [APP_NAME] + ctx_path_parts[1:]
        else:
            command_parts = ctx_path_parts

        # Build the new help text starting with Usage
        new_help = [
            f"{styler.usage_command_help('Usage:')} {styler.usage_command_name(' '.join(command_parts))}"
        ]

        # Add arguments to usage line
        usage_parts = []
        if positional_args:
            usage_parts.extend(styler.argument_required_name(param.name.upper()) for param in positional_args)
        if required_options:
            usage_parts.append(styler.option_required_name("REQUIRED_OPTIONS"))
        if optional_options:
            usage_parts.append(styler.option_optional_name("[OPTIONS]"))

        if usage_parts:
            new_help[0] += " " + " ".join(usage_parts)

        # Add description and rest of the help text
        if description:
            new_help.extend([
                '',
                styler.usage_command_help(description)
            ])

        # Add positional arguments section
        if positional_args:
            section_text = 'Positional Arguments:'
            new_help.extend([
                '',
                styler.argument_required_header(section_text),
                styler.argument_required_divider('-', len(section_text))
            ])
            sorted_positional_args = sorted(
                positional_args,
                key=lambda param: (
                    not getattr(param, 'required', True),
                    param.name
                )
            )
            for param in sorted_positional_args:
                new_help.append(self._format_argument(param))

        # Add required options section
        if required_options:
            section_text = 'Required Options:'
            new_help.extend([
                '',
                styler.option_required_header(section_text),
                styler.option_required_divider('-', len(section_text))
            ])
            for param in required_options:
                new_help.append(self._format_option(param, required=True))

        # Add optional options section
        if optional_options:
            section_text = 'Options:'
            new_help.extend([
                '',
                styler.option_optional_header(section_text),
                styler.option_optional_divider('-', len(section_text))
            ])
            for param in optional_options:
                new_help.append(self._format_option(param, required=False))

        # Add examples section
        section_text = 'Examples:'
        new_help.extend([
            '',
            styler.example_command_header(section_text),
            styler.example_command_divider('-', len(section_text)),
            self._format_examples(positional_args, required_options)
        ])

        return '\n'.join(new_help)

    def _format_argument(self, param: Argument) -> str:
        """Format a positional argument for the help output."""
        required = getattr(param, 'required', True)

        # Get help text
        help_text = self.argument_help_texts.get(param.name, '')

        # Add required indicator
        if required:
            name = styler.argument_required_name(param.name.upper())
            help_str = styler.argument_required_help(help_text)
            help_str += styler.argument_required_metavar(' (Required)')
        else:
            help_str = styler.argument_optional_help(help_text)
            name = styler.argument_optional_header(param.name.upper())

        # Add multiple indicator
        if getattr(param, 'nargs', 1) < 0 or getattr(param, 'multiple', False):
            help_str += (styler.argument_required_metavar(' (Multiple)') if required
                         else styler.argument_optional_metavar(' (Multiple)'))

        # Add default value
        if param.default is not None and not param.required:
            help_str += (styler.argument_required_default(f' (default: {param.default})') if required
                         else styler.argument_optional_default(f' (default: {param.default})'))

        # Calculate and align text
        description_start = len(INDENT) + OPTION_WIDTH + OPTION_PADDING
        available_width = TOTAL_WIDTH - description_start
        help_parts = wrap_text(help_str, available_width)
        return self._align_text(name, help_parts, description_start)

    def _format_option(self, param: Option, required: bool = False) -> str:
        """Format an option for the help output."""
        opts = []
        for opt in param.opts + param.secondary_opts:
            opts.append(opt)

        # Choose the appropriate styling based on whether the option is required
        if required:
            opt_str = styler.option_required_name(', '.join(opts))
            help_str = styler.option_required_help(param.help or '')
            help_str += styler.option_required_metavar(' (Required)')
        else:
            opt_str = styler.option_optional_name(', '.join(opts))
            help_str = styler.option_optional_help(param.help or '')

        # Add multiple indicator
        if getattr(param, 'multiple', False):
            help_str += (styler.option_required_metavar(' (Multiple)') if required
                         else styler.option_optional_metavar(' (Multiple)'))

        # Add choices
        if hasattr(param, 'type') and hasattr(param.type, 'choices') and param.type.choices:
            choices_str = f" (Choices: {', '.join(param.type.choices)})"
            help_str += (styler.option_required_metavar(choices_str) if required
                         else styler.option_optional_metavar(choices_str))

        # Add default value
        if param.default is not None and str(param.default) != '' and not param.required:
            default_str = f' (default: {param.default})'
            help_str += (styler.option_required_default(default_str) if required
                         else styler.option_optional_default(default_str))

        # Calculate and align text
        description_start = len(INDENT) + OPTION_WIDTH + OPTION_PADDING
        available_width = TOTAL_WIDTH - description_start
        help_parts = wrap_text(help_str, available_width)
        return self._align_text(opt_str, help_parts, description_start)

    def _align_text(self, opt_str: str, help_parts: List[str], description_start: int) -> str:
        """Align option and help text parts."""
        option_part = f"{INDENT}{opt_str}"
        visual_length = get_visual_length(option_part)
        padding_needed = description_start - visual_length

        first_line = f"{option_part}{' ' * padding_needed}{help_parts[0]}"

        if len(help_parts) == 1:
            return first_line + "\n"

        result = [first_line]
        description_padding = ' ' * description_start
        result.extend(f"{description_padding}{part}" for part in help_parts[1:])
        return '\n'.join(result) + "\n"

    def _format_examples(self, positional_args: List[Parameter], required_options: List[Parameter]) -> str:
        """Format command examples with proper styling."""
        ctx = click.get_current_context()
        command_path_parts = []
        current_ctx = ctx

        while current_ctx.parent is not None:
            if current_ctx.command.name != '':
                command_path_parts.insert(0, current_ctx.command.name)
            current_ctx = current_ctx.parent

        command_path = ' '.join(
            styler.example_command_name(part) for part in command_path_parts
        )

        positional_part = ' '.join(
            styler.argument_optional_name(f"{param.name.upper()}{' [...]' if getattr(param, 'multiple', False) else ''}")
            for param in positional_args
            if getattr(param, 'required', True)
        )

        required_part = ' '.join(
            styler.option_required_name(f"--{param.name.replace('_', '-')} VALUE{' [...]' if getattr(param, 'multiple', False) else ''}")
            for param in required_options
        )

        parts = [command_path]
        if positional_part:
            parts.append(positional_part)
        if required_part:
            parts.append(required_part)

        examples = []
        if len(parts) > 1:
            examples.append(f"  $ {APP_NAME} {' '.join(parts)}")
        else:
            examples.append(f"  $ {APP_NAME} {command_path} [OPTIONS]")

        examples.append(f"  $ {APP_NAME} {command_path} {styler.option_optional_name('--help')}")

        return styler.example_command_help('\n'.join(examples))
