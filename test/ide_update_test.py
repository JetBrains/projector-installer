"""Test ide_update.py module"""
from unittest import TestCase
from projector_installer.ide_update import is_updatable_ide


class IdeUpdateTest(TestCase):
    """Test ide_update.py module"""

    def test_is_updatable_ide_false(self) -> None:
        """The is_updatable_ide method must return false if the path to ide is incorrect"""
        self.assertFalse(is_updatable_ide(path_to_ide='incorrect_path'))
