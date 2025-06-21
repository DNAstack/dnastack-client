from dataclasses import dataclass
from typing import Dict, Optional
import os
import subprocess
import platform
from functools import lru_cache
import click

from dnastack.common.logger import get_logger

@dataclass
class TerminalTheme:
    """Theme configuration for terminal output"""

    # Message types
    error: Dict[str, Optional[str]]
    warning: Dict[str, Optional[str]]
    success: Dict[str, Optional[str]]
    info: Dict[str, Optional[str]]
    debug: Dict[str, Optional[str]]

    # Usage command styling
    usage_command_name: Dict[str, Optional[str]]  # fg, bg, bold, underline, etc
    usage_command_help: Dict[str, Optional[str]]

    # Example command styling
    example_command_header: Dict[str, Optional[str]]
    example_command_divider: Dict[str, Optional[str]]
    example_command_name: Dict[str, Optional[str]]
    example_command_help: Dict[str, Optional[str]]

    # Command styling
    command_header: Dict[str, Optional[str]]
    command_divider: Dict[str, Optional[str]]
    command_name: Dict[str, Optional[str]]
    command_alias: Dict[str, Optional[str]]
    command_help: Dict[str, Optional[str]]

    # Required positional argument styling
    argument_required_header: Dict[str, Optional[str]]
    argument_required_divider: Dict[str, Optional[str]]
    argument_required_name: Dict[str, Optional[str]]
    argument_required_metavar: Dict[str, Optional[str]]
    argument_required_help: Dict[str, Optional[str]]
    argument_required_default: Dict[str, Optional[str]]

    # Optional positional argument styling
    argument_optional_header: Dict[str, Optional[str]]
    argument_optional_divider: Dict[str, Optional[str]]
    argument_optional_name: Dict[str, Optional[str]]
    argument_optional_metavar: Dict[str, Optional[str]]
    argument_optional_help: Dict[str, Optional[str]]
    argument_optional_default: Dict[str, Optional[str]]

    # Required options styling
    option_required_header: Dict[str, Optional[str]]
    option_required_divider: Dict[str, Optional[str]]
    option_required_name: Dict[str, Optional[str]]
    option_required_metavar: Dict[str, Optional[str]]
    option_required_help: Dict[str, Optional[str]]
    option_required_default: Dict[str, Optional[str]]

    # Optional options styling
    option_optional_header: Dict[str, Optional[str]]
    option_optional_divider: Dict[str, Optional[str]]
    option_optional_name: Dict[str, Optional[str]]
    option_optional_metavar: Dict[str, Optional[str]]
    option_optional_help: Dict[str, Optional[str]]
    option_optional_default: Dict[str, Optional[str]]


# Default theme configurations
LIGHT_THEME = TerminalTheme(
    # Message types
    error={'fg': 'red', 'bold': True},
    warning={'fg': 'yellow'},
    success={'fg': 'green'},
    info={'fg': 'black'},
    debug={'fg': 'dark_gray'},

    # Usage command help styling
    usage_command_name={'fg': 'black', 'bold': True},
    usage_command_help={'fg': 'black'},

    # Example command styling
    example_command_header={'fg': 'black', 'bold': True},
    example_command_divider={'fg': 'black'},
    example_command_name={'fg': 'black', 'bold': True},
    example_command_help={'fg': 'black'},

    # Command styling
    command_header={'fg': 'blue', 'bold': True},
    command_divider={'fg': 'blue'},
    command_name={'fg': 'blue', 'bold': True},
    command_alias={'fg': 'blue', 'bold': False},
    command_help={'fg': 'black'},

    # Required positional argument styling
    argument_required_header={'fg': 'magenta', 'bold': True},
    argument_required_divider={'fg': 'magenta'},
    argument_required_name={'fg': 'magenta', 'bold': True},
    argument_required_metavar={'fg': 'black', 'bold': True},
    argument_required_help={'fg': 'black'},
    argument_required_default={'fg': 'black'},

    # Optional positional argument styling
    argument_optional_header={'fg': 'magenta', 'bold': True},
    argument_optional_divider={'fg': 'magenta'},
    argument_optional_name={'fg': 'magenta', 'bold': True},
    argument_optional_metavar={'fg': 'black', 'bold': True},
    argument_optional_help={'fg': 'black'},
    argument_optional_default={'fg': 'black'},

    # Required options styling
    option_required_header={'fg': 'bright_red', 'bold': True},
    option_required_divider={'fg': 'bright_red'},
    option_required_name={'fg': 'bright_red', 'bold': True},
    option_required_metavar={'fg': 'black', 'bold': True},
    option_required_help={'fg': 'black'},
    option_required_default={'fg': 'black'},

    # Optional options styling
    option_optional_header={'fg': 'yellow', 'bold': True},
    option_optional_divider={'fg': 'yellow'},
    option_optional_name={'fg': 'yellow', 'bold': True},
    option_optional_metavar={'fg': 'black', 'bold': True},
    option_optional_help={'fg': 'black'},
    option_optional_default={'fg': 'black'},
)

DARK_THEME = TerminalTheme(
    # Message types
    error={'fg': 'red', 'bold': True},
    warning={'fg': 'yellow'},
    success={'fg': 'green'},
    info={'fg': 'white'},
    debug={'fg': 'bright_black'},

    # Usage command help styling
    usage_command_name={'fg': 'white', 'bold': True},
    usage_command_help={'fg': 'white'},

    # Example command styling
    example_command_header={'fg': 'white', 'bold': True},
    example_command_divider={'fg': 'white'},
    example_command_name={'fg': 'white', 'bold': True},
    example_command_help={'fg': 'white'},

    # Command styling
    command_header={'fg': 'blue', 'bold': True},
    command_divider={'fg': 'blue'},
    command_name={'fg': 'blue', 'bold': True},
    command_alias={'fg': 'blue', 'bold': False},
    command_help={'fg': 'white'},

    # Required positional argument styling
    argument_required_header={'fg': 'magenta', 'bold': True},
    argument_required_divider={'fg': 'magenta'},
    argument_required_name={'fg': 'magenta', 'bold': True},
    argument_required_metavar={'fg': 'white', 'bold': True},
    argument_required_help={'fg': 'white'},
    argument_required_default={'fg': 'white'},

    # Optional positional argument styling
    argument_optional_header={'fg': 'magenta', 'bold': True},
    argument_optional_divider={'fg': 'magenta'},
    argument_optional_name={'fg': 'magenta', 'bold': True},
    argument_optional_metavar={'fg': 'white', 'bold': True},
    argument_optional_help={'fg': 'white'},
    argument_optional_default={'fg': 'white'},

    # Required options styling
    option_required_header={'fg': 'bright_red', 'bold': True},
    option_required_divider={'fg': 'bright_red'},
    option_required_name={'fg': 'bright_red', 'bold': True},
    option_required_metavar={'fg': 'white', 'bold': True},
    option_required_help={'fg': 'white'},
    option_required_default={'fg': 'white'},

    # Optional options styling
    option_optional_header={'fg': 'yellow', 'bold': True},
    option_optional_divider={'fg': 'yellow'},
    option_optional_name={'fg': 'yellow', 'bold': True},
    option_optional_metavar={'fg': 'white', 'bold': True},
    option_optional_help={'fg': 'white'},
    option_optional_default={'fg': 'white'},
)

class ThemeManager:
    def __init__(self):
        self._logger = get_logger('ThemeManager')
        self._current_theme: Optional[TerminalTheme] = None

    @lru_cache(maxsize=1)
    def detect_theme(self) -> TerminalTheme:
        """Detect and return appropriate theme based on terminal background"""
        if self._is_light_terminal():
            self._logger.debug("Detected light terminal theme")
            return LIGHT_THEME
        self._logger.debug("Detected dark terminal theme")
        return DARK_THEME

    def _is_light_terminal(self) -> bool:
        """Detect if terminal has light background using multiple methods"""
        system = platform.system()

        # Try specific terminal app detection first
        terminal_app = self._detect_terminal_app()
        if terminal_app:
            self._logger.debug(f"Detected terminal app: {terminal_app}")
            return self._is_light_terminal_app(terminal_app)

        # macOS system-wide detection
        if system == "Darwin":
            try:
                # Try Terminal.app specific detection first
                if 'TERM_PROGRAM' in os.environ and os.environ['TERM_PROGRAM'] == 'Apple_Terminal':
                    try:
                        result = subprocess.run(
                            ['osascript', '-e', 'tell application "Terminal" to get background color of selected tab of front window'],
                            capture_output=True,
                            text=True
                        )
                        if result.returncode == 0:
                            # Parse RGB values - higher values indicate lighter background
                            rgb_values = [int(x) for x in result.stdout.strip().split(",")]
                            brightness = sum(rgb_values) / (255 * 3)  # Normalize to 0-1
                            return brightness > 0.5
                    except Exception as e:
                        self._logger.debug(f"Failed to detect Terminal.app theme: {e}")

                # Try system-wide dark mode setting
                result = subprocess.run(
                    ['defaults', 'read', '-g', 'AppleInterfaceStyle'],
                    capture_output=True,
                    text=True
                )
                # Check both return code and actual output
                is_dark = result.returncode == 0 and 'Dark' in result.stdout
                return not is_dark

            except Exception as e:
                self._logger.debug(f"Failed to detect macOS theme: {e}")

        # Windows detection
        elif system == "Windows":
            try:
                cmd = 'Get-ItemProperty -Path "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize" -Name "AppsUseLightTheme"'
                result = subprocess.run(['powershell', '-Command', cmd],
                                        capture_output=True,
                                        text=True,
                                        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0)
                return bool("1" in result.stdout) if result.returncode == 0 else False
            except Exception as e:
                self._logger.debug(f"Failed to detect Windows theme: {e}")

        # Try environment variables
        terminal_bg = self._detect_from_env()
        if terminal_bg is not None:
            return terminal_bg

        # Default to dark theme
        self._logger.debug("Could not detect theme, defaulting to dark theme")
        return False

    def _detect_terminal_app(self) -> Optional[str]:
        """Detect which terminal app is being used"""
        if 'TERM_PROGRAM' in os.environ:
            return os.environ['TERM_PROGRAM']
        elif 'TERMINAL_EMULATOR' in os.environ:
            return os.environ['TERMINAL_EMULATOR']
        return None

    def _is_light_terminal_app(self, terminal_app: str) -> bool:
        """Check if specific terminal app is using light theme"""
        terminal_app = terminal_app.lower()

        if 'iterm' in terminal_app:
            try:
                # Try to get iTerm2 profile info
                result = subprocess.run(
                    ['osascript', '-e', 'tell application "iTerm2" to get background color of current session of current window'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    # Parse RGB values
                    rgb_values = [int(x) for x in result.stdout.strip().split(",")]
                    brightness = sum(rgb_values) / (255 * 3)
                    return brightness > 0.5
            except Exception as e:
                self._logger.debug(f"Failed to detect iTerm2 theme: {e}")

        elif 'vscode' in terminal_app:
            # VSCode sets these environment variables
            if 'VSCODE_TERMINAL_THEME_KIND' in os.environ:
                return os.environ['VSCODE_TERMINAL_THEME_KIND'] == 'light'

        return False

    def _detect_from_env(self) -> Optional[bool]:
        """Detect theme from environment variables"""
        # Try COLORFGBG
        if 'COLORFGBG' in os.environ:
            try:
                fg_bg = os.environ['COLORFGBG'].split(';')
                if len(fg_bg) >= 2:
                    bg_color = int(fg_bg[-1])
                    return bg_color > 7
            except Exception as e:
                self._logger.debug(f"Failed to parse COLORFGBG: {e}")

        # Try NO_COLOR
        if 'NO_COLOR' in os.environ:
            return False  # Assume dark theme if NO_COLOR is set

        # Try COLORTERM
        if 'COLORTERM' in os.environ:
            if os.environ['COLORTERM'] in ('light', 'white'):
                return True
            elif os.environ['COLORTERM'] in ('dark', 'black'):
                return False

        return None

    def get_current_theme(self) -> TerminalTheme:
        """Get current theme, detecting if not already set"""
        if not self._current_theme:
            self._current_theme = self.detect_theme()
        return self._current_theme

    def set_theme(self, theme: TerminalTheme):
        """Manually set theme"""
        self._current_theme = theme

    def style(self, text: str, style_key: str, **kwargs) -> str:
        """Style text according to current theme and style key"""
        if text is None:
            self._logger.warning(f"Received None text for style_key '{style_key}'")
            return ''

        theme = self.get_current_theme()
        if hasattr(theme, style_key):
            style_dict = getattr(theme, style_key)
            # Remove echo-specific keywords that shouldn't go to style
            style_kwargs = {k: v for k, v in {**style_dict, **kwargs}.items()
                            if k not in ('err', 'nl', 'file')}
            try:
                return click.style(str(text), **style_kwargs)
            except Exception as e:
                self._logger.error(f"Error styling text '{text}' with style '{style_key}': {e}")
                return str(text)
        return str(text)

    def echo(self, text: str, style_key: str, **kwargs):
        """Print styled text according to current theme"""
        # Separate echo kwargs from style kwargs
        echo_kwargs = {k: kwargs.pop(k) for k in ('err', 'nl', 'file')
                       if k in kwargs}
        # Style the text and then echo it
        styled_text = self.style(text, style_key, **kwargs)
        click.echo(styled_text, **echo_kwargs)

# Global theme manager instance
theme_manager = ThemeManager()
