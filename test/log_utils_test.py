"""Test log_utils.py module"""
from unittest import TestCase
from projector_installer.log_utils import is_unexpected_exit


class LogUtilsTest(TestCase):
    """Test log_utils.py module"""

    def test_is_unexpected_exit(self) -> None:
        """The is_unexpected_exit method must return true if ret_code is not in [0, -2, -15]"""
        self.assertTrue(is_unexpected_exit(ret_code=1))
        self.assertFalse(is_unexpected_exit(ret_code=0))
        self.assertFalse(is_unexpected_exit(ret_code=-2))
        self.assertFalse(is_unexpected_exit(ret_code=-15))
