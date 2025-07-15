import unittest

from dnastack.cli.core.command_formatting import FormattedHelpCommand


class TestFormattedHelpCommand(unittest.TestCase):
    """Unit tests for FormattedHelpCommand class focusing on constants usage."""

    def setUp(self):
        """Set up test fixtures."""
        self.command = FormattedHelpCommand(
            name="test-command",
            help="A test command for unit testing"
        )

    def test_init_sets_context_settings(self):
        """Test that __init__ properly sets context settings."""
        expected_settings = {
            'help_option_names': ['-h', '--help'],
            'token_normalize_func': self.command.context_settings['token_normalize_func']
        }
        
        self.assertEqual(self.command.context_settings['help_option_names'], expected_settings['help_option_names'])
        self.assertIsNotNone(self.command.context_settings['token_normalize_func'])
        
        # Test token normalization function
        normalize_func = self.command.context_settings['token_normalize_func']
        self.assertEqual(normalize_func('TEST'), 'test')

    def test_store_and_retrieve_argument_help(self):
        """Test storing and retrieving argument help texts."""
        self.command.store_argument_help("input_file", "Path to input file")
        self.assertEqual(self.command.argument_help_texts["input_file"], "Path to input file")

    def test_align_text_uses_constants(self):
        """Test that _align_text method uses the imported constants correctly."""
        # Test data - this method directly uses INDENT constant
        opt_str = "--verbose"
        help_parts = ["Enable verbose output", "for debugging purposes"]
        description_start = 34  # len(INDENT) + OPTION_WIDTH + OPTION_PADDING
        
        # Call the method under test
        result = self.command._align_text(opt_str, help_parts, description_start)
        
        # Verify the result is properly formatted
        self.assertIsInstance(result, str)
        self.assertIn("--verbose", result)
        self.assertIn("Enable verbose output", result)
        self.assertIn("for debugging purposes", result)

    def test_constants_are_accessible(self):
        """Test that all required constants are accessible in the module."""
        from dnastack.cli.core import command_formatting
        
        # These constants should be available after the star import
        # This test will fail if the star import replacement breaks access
        self.assertTrue(hasattr(command_formatting, 'APP_NAME'))
        self.assertTrue(hasattr(command_formatting, 'INDENT'))
        self.assertTrue(hasattr(command_formatting, 'OPTION_WIDTH'))
        self.assertTrue(hasattr(command_formatting, 'OPTION_PADDING'))
        self.assertTrue(hasattr(command_formatting, 'TOTAL_WIDTH'))

    def test_constants_have_expected_values(self):
        """Test that constants have the expected types and reasonable values."""
        from dnastack.cli.core import command_formatting
        
        # Test that constants are the right type and have reasonable values
        self.assertIsInstance(command_formatting.APP_NAME, str)
        self.assertIsInstance(command_formatting.INDENT, str)
        self.assertIsInstance(command_formatting.OPTION_WIDTH, int)
        self.assertIsInstance(command_formatting.OPTION_PADDING, int)
        self.assertIsInstance(command_formatting.TOTAL_WIDTH, int)
        
        # Check reasonable values
        self.assertEqual(command_formatting.INDENT, "  ")  # 2 spaces
        self.assertEqual(command_formatting.OPTION_WIDTH, 30)
        self.assertEqual(command_formatting.OPTION_PADDING, 2)
        self.assertEqual(command_formatting.TOTAL_WIDTH, 120)

    def test_constants_calculation_in_methods(self):
        """Test that methods using constants work correctly."""
        from dnastack.cli.core.constants import INDENT, OPTION_WIDTH, OPTION_PADDING, TOTAL_WIDTH
        
        # Test the calculation that appears in the code
        description_start = len(INDENT) + OPTION_WIDTH + OPTION_PADDING
        available_width = TOTAL_WIDTH - description_start
        
        # These should be reasonable values
        self.assertEqual(description_start, 34)  # 2 + 30 + 2
        self.assertEqual(available_width, 86)    # 120 - 34
        
        # Test _align_text with these calculated values
        result = self.command._align_text("--test", ["Help text"], description_start)
        self.assertIsInstance(result, str)
        self.assertIn("--test", result)
        self.assertIn("Help text", result)


if __name__ == '__main__':
    unittest.main()