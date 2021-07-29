"""Test config_generator.py module"""
from unittest import TestCase

from projector_installer.config_generator import token_quote


class ConfigGeneratorTest(TestCase):
    """Test config_generator.py module"""

    def test_token_quote(self) -> None:
        """The token_quote method must return the same token in quotes"""
        self.assertEqual(token_quote('some_token'), '\"some_token\"')
