from typing import Any

from .themes import theme_manager

class CLIStyler:
    @staticmethod
    def _ensure_str(text: Any) -> str:
        """Ensure the input is converted to a string"""
        return str(text) if text is not None else ''

    # Usage command styling
    @staticmethod
    def usage_command_name(text: str) -> str:
        return theme_manager.style(CLIStyler._ensure_str(text), 'usage_command_name')

    @staticmethod
    def usage_command_help(text: str) -> str:
        return theme_manager.style(CLIStyler._ensure_str(text), 'usage_command_help')

    # Example command styling
    @staticmethod
    def example_command_header(text: str) -> str:
        return theme_manager.style(CLIStyler._ensure_str(text), 'example_command_header')

    @staticmethod
    def example_command_name(text: str) -> str:
        return theme_manager.style(CLIStyler._ensure_str(text), 'example_command_name')

    @staticmethod
    def example_command_help(text: str) -> str:
        return theme_manager.style(CLIStyler._ensure_str(text), 'example_command_help')

    @staticmethod
    def example_command_divider(char: str, length: int = 80, **kwargs) -> str:
        text = char * length
        return theme_manager.style(CLIStyler._ensure_str(text), 'example_command_divider', **kwargs)

    # Command styling
    @staticmethod
    def command_header(text: str) -> str:
        return theme_manager.style(CLIStyler._ensure_str(text), 'command_header')

    @staticmethod
    def command_name(text: str) -> str:
        return theme_manager.style(CLIStyler._ensure_str(text), 'command_name')

    @staticmethod
    def command_divider(char: str, length: int = 80, **kwargs) -> str:
        text = char * length
        return theme_manager.style(CLIStyler._ensure_str(text), 'command_divider', **kwargs)

    @staticmethod
    def command_alias(text: str) -> str:
        return theme_manager.style(CLIStyler._ensure_str(text), 'command_alias')

    @staticmethod
    def command_help(text: str) -> str:
        return theme_manager.style(CLIStyler._ensure_str(text), 'command_help')

    # Required positional arguments styling
    @staticmethod
    def argument_required_header(text: str) -> str:
        return theme_manager.style(CLIStyler._ensure_str(text), 'argument_required_header')

    @staticmethod
    def argument_required_divider(char: str, length: int = 80, **kwargs) -> str:
        text = char * length
        return theme_manager.style(CLIStyler._ensure_str(text), 'argument_required_divider', **kwargs)

    @staticmethod
    def argument_required_name(text: str) -> str:
        return theme_manager.style(CLIStyler._ensure_str(text), 'argument_required_name')

    @staticmethod
    def argument_required_metavar(text: str) -> str:
        return theme_manager.style(CLIStyler._ensure_str(text), 'argument_required_metavar')

    @staticmethod
    def argument_required_help(text: str) -> str:
        return theme_manager.style(CLIStyler._ensure_str(text), 'argument_required_help')

    @staticmethod
    def argument_required_default(text: str) -> str:
        return theme_manager.style(CLIStyler._ensure_str(text), 'argument_required_default')

    # Optional positional arguments styling
    @staticmethod
    def argument_optional_header(text: str) -> str:
        return theme_manager.style(CLIStyler._ensure_str(text), 'argument_optional_header')

    @staticmethod
    def argument_optional_divider(char: str, length: int = 80, **kwargs) -> str:
        text = char * length
        return theme_manager.style(CLIStyler._ensure_str(text), 'argument_optional_divider', **kwargs)

    @staticmethod
    def argument_optional_name(text: str) -> str:
        return theme_manager.style(CLIStyler._ensure_str(text), 'argument_optional_name')

    @staticmethod
    def argument_optional_metavar(text: str) -> str:
        return theme_manager.style(CLIStyler._ensure_str(text), 'argument_optional_metavar')

    @staticmethod
    def argument_optional_help(text: str) -> str:
        return theme_manager.style(CLIStyler._ensure_str(text), 'argument_optional_help')

    @staticmethod
    def argument_optional_default(text: str) -> str:
        return theme_manager.style(CLIStyler._ensure_str(text), 'argument_optional_default')

    # Required options styling
    @staticmethod
    def option_required_header(text: str) -> str:
        return theme_manager.style(CLIStyler._ensure_str(text), 'option_required_header')

    @staticmethod
    def option_required_divider(char: str, length: int = 80, **kwargs) -> str:
        text = char * length
        return theme_manager.style(CLIStyler._ensure_str(text), 'option_required_divider', **kwargs)

    @staticmethod
    def option_required_name(text: str) -> str:
        return theme_manager.style(CLIStyler._ensure_str(text), 'option_required_name')

    @staticmethod
    def option_required_metavar(text: str) -> str:
        return theme_manager.style(CLIStyler._ensure_str(text), 'option_required_metavar')

    @staticmethod
    def option_required_help(text: str) -> str:
        return theme_manager.style(CLIStyler._ensure_str(text), 'option_required_help')

    @staticmethod
    def option_required_default(text: str) -> str:
        return theme_manager.style(CLIStyler._ensure_str(text), 'option_required_default')

    # Optional options styling
    @staticmethod
    def option_optional_header(text: str) -> str:
        return theme_manager.style(CLIStyler._ensure_str(text), 'option_optional_header')

    @staticmethod
    def option_optional_divider(char: str, length: int = 80, **kwargs) -> str:
        text = char * length
        return theme_manager.style(CLIStyler._ensure_str(text), 'option_optional_divider', **kwargs)

    @staticmethod
    def option_optional_name(text: str) -> str:
        return theme_manager.style(CLIStyler._ensure_str(text), 'option_optional_name')

    @staticmethod
    def option_optional_metavar(text: str) -> str:
        return theme_manager.style(CLIStyler._ensure_str(text), 'option_optional_metavar')

    @staticmethod
    def option_optional_help(text: str) -> str:
        return theme_manager.style(CLIStyler._ensure_str(text), 'option_optional_help')

    @staticmethod
    def option_optional_default(text: str) -> str:
        return theme_manager.style(CLIStyler._ensure_str(text), 'option_optional_default')

    @staticmethod
    def error(message: str, as_text: bool = False, **kwargs) -> str:
        text = CLIStyler._ensure_str(message)
        if as_text:
            return theme_manager.style(text, 'error', **kwargs)
        theme_manager.echo(text, 'error', err=True, **kwargs)
        return text

    @staticmethod
    def warning(message: str, as_text: bool = False, **kwargs) -> str:
        text = CLIStyler._ensure_str(message)
        if as_text:
            return theme_manager.style(text, 'warning', **kwargs)
        theme_manager.echo(text, 'warning', err=True, **kwargs)
        return text

    @staticmethod
    def success(message: str, as_text: bool = False, **kwargs) -> str:
        text = CLIStyler._ensure_str(message)
        if as_text:
            return theme_manager.style(text, 'success', **kwargs)
        theme_manager.echo(text, 'success', **kwargs)
        return text

    @staticmethod
    def info(message: str, as_text: bool = False, **kwargs) -> str:
        text = CLIStyler._ensure_str(message)
        if as_text:
            return theme_manager.style(text, 'info', **kwargs)
        theme_manager.echo(text, 'info', **kwargs)
        return text

    @staticmethod
    def debug(message: str, as_text: bool = False, **kwargs) -> str:
        text = CLIStyler._ensure_str(message)
        if as_text:
            return theme_manager.style(text, 'debug', **kwargs)
        theme_manager.echo(text, 'debug', **kwargs)
        return text


# Global styler instance
styler = CLIStyler()

# Convenience exports
error = styler.error
warning = styler.warning
success = styler.success
info = styler.info
debug = styler.debug
