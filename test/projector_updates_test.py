"""Test projector_updates.py module"""
from unittest import TestCase

from projector_installer.projector_updates import is_newer_than_current
from projector_installer.version import __version__


class ProjectorUpdatesTest(TestCase):
    """Test projector_updates.py module"""

    def test_is_newer_than_current_true(self) -> None:
        """The is_newer_than_current method must return true if a newer version is provided"""
        first_digit = __version__[0:__version__.find('.')]
        new_first_digit = int(first_digit) + 1
        newer_version = __version__.replace(first_digit, str(new_first_digit))

        self.assertTrue(is_newer_than_current(newer_version))

    def test_is_newer_than_current_false(self) -> None:
        """The is_newer_than_current method must return false if an older version is provided"""
        first_digit = __version__[0:__version__.find('.')]
        new_first_digit = int(first_digit) - 1
        newer_version = __version__.replace(first_digit, str(new_first_digit))

        self.assertFalse(is_newer_than_current(newer_version))

    def test_is_newer_than_current_same_version(self) -> None:
        """The is_newer_than_current method must return false if the same version is provided"""
        self.assertFalse(is_newer_than_current(__version__))
