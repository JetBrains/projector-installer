"""Test secure_config.py module"""

from unittest import TestCase

from projector_installer.secure_config import get_ca_password


class SecureConfigTest(TestCase):
    """Test secure_config.py module"""

    def test_get_ca_password(self) -> None:
        """The get_ca_password method must return ca password"""
        self.assertEqual(get_ca_password(), '85TibAyPS3NZX3')
