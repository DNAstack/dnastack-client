import unittest
from unittest.mock import Mock, patch

# Test core functions that exist and work
from dnastack.cli.commands.explorer.questions.utils import (
    parse_collections_argument,
    flatten_result_for_export
)


class TestExplorerMinimal(unittest.TestCase):
    """Minimal tests to achieve coverage goals"""

    def test_parse_collections_none(self):
        """Test parsing None collections"""
        result = parse_collections_argument(None)
        self.assertIsNone(result)

    def test_parse_collections_empty(self):
        """Test parsing empty collections"""
        result = parse_collections_argument("")
        self.assertIsNone(result)

    def test_parse_collections_single(self):
        """Test parsing single collection"""
        result = parse_collections_argument("collection1")
        self.assertEqual(result, ["collection1"])

    def test_parse_collections_multiple(self):
        """Test parsing multiple collections"""
        result = parse_collections_argument("collection1,collection2")
        self.assertEqual(result, ["collection1", "collection2"])

    def test_parse_collections_with_spaces(self):
        """Test parsing collections with spaces"""
        result = parse_collections_argument(" collection1 , collection2 ")
        self.assertEqual(result, ["collection1", "collection2"])

    def test_flatten_result_simple(self):
        """Test flattening simple result"""
        result = {"name": "John", "age": 30}
        flattened = flatten_result_for_export(result)
        self.assertEqual(flattened, {"name": "John", "age": 30})

    def test_flatten_result_nested(self):
        """Test flattening nested result"""
        result = {"person": {"name": "John", "age": 30}}
        flattened = flatten_result_for_export(result)
        self.assertEqual(flattened, {"person.name": "John", "person.age": 30})

    def test_flatten_result_with_list(self):
        """Test flattening result with list"""
        result = {"names": ["John", "Jane"]}
        flattened = flatten_result_for_export(result)
        self.assertEqual(flattened, {"names[0]": "John", "names[1]": "Jane"})

    def test_flatten_result_complex(self):
        """Test flattening complex nested structures"""
        result = {
            "level1": {
                "level2": {
                    "value": "deep_value"
                },
                "list": [{"item": "value1"}, {"item": "value2"}]
            }
        }
        flattened = flatten_result_for_export(result)
        self.assertIn("level1.level2.value", flattened)
        self.assertIn("level1.list[0].item", flattened)
        self.assertEqual(flattened["level1.level2.value"], "deep_value")

    @patch('dnastack.cli.commands.explorer.questions.utils.container.get')
    def test_get_explorer_client_basic(self, mock_container_get):
        """Test getting explorer client"""
        from dnastack.cli.commands.explorer.questions.utils import get_explorer_client
        
        mock_factory = Mock()
        mock_client = Mock()
        mock_factory.get.return_value = mock_client
        mock_container_get.return_value = mock_factory

        result = get_explorer_client()
        
        self.assertEqual(result, mock_client)
        mock_factory.get.assert_called_once()

    @patch('dnastack.cli.commands.explorer.questions.utils.container.get')
    def test_get_explorer_client_with_params(self, mock_container_get):
        """Test getting explorer client with parameters"""
        from dnastack.cli.commands.explorer.questions.utils import get_explorer_client
        
        mock_factory = Mock()
        mock_client = Mock()
        mock_factory.get.return_value = mock_client
        mock_container_get.return_value = mock_factory

        result = get_explorer_client(context="test", endpoint_id="endpoint1")
        
        self.assertEqual(result, mock_client)
        mock_factory.get.assert_called_once()


if __name__ == '__main__':
    unittest.main()