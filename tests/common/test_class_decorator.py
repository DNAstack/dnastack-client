from time import time
from typing import Optional, Any, Callable
from unittest import TestCase

from dnastack.common.class_decorator import simple_constructor, UndefinedInitializedPropertyError


@simple_constructor()
class AlphaService:
    url: str
    enabled: Optional[bool] = None
    processor: Callable[[Any], bool]
    after_init: Optional[Callable[[Any], bool]] = None
    activated_at = time()


class UnitTest(TestCase):
    def test_happy_path(self):
        with self.assertRaises(UndefinedInitializedPropertyError):
            AlphaService()

        sample = AlphaService(url='http://foo.com', processor=lambda x: x)

        self.assertEqual(sample.url, 'http://foo.com')
        self.assertIsNone(sample.enabled)
        self.assertIsNotNone(sample.processor)
        self.assertIsNone(sample.after_init)
        self.assertGreater(sample.activated_at, 0)

    def test_handle_required_fields(self):
        with self.assertRaises(UndefinedInitializedPropertyError):
            AlphaService()

        with self.assertRaises(UndefinedInitializedPropertyError):
            AlphaService(url='http://foo.com')
