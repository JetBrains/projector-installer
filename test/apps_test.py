"""Test apps.py module"""
from unittest import TestCase
from os.path import join, expanduser
import pytest

from projector_installer.apps import get_app_path, is_path_to_app, parse_version, \
    get_data_dir_from_script, is_mps_dir


class AppsTest(TestCase):
    """Test apps.py module"""

    app_path = join(expanduser('~'), 'projector/apps/app_path')

    def test_get_app_path(self):
        """The get_app_path method must return correct full path for the specified app path"""
        user = expanduser('~')
        self.assertEqual(get_app_path("app_path"), f'{user}/.projector/apps/app_path')

    def test_is_path_to_app_false(self):
        """The is_path_to_app method must return false if the specified app doesn't exist"""
        self.assertFalse(is_path_to_app(self.app_path))

    # The parse_version method gives an error when version is a number, for example, 2020124
    # Is that normal? Can we get a version consisting of digits only?
    def test_parse_version_false(self):
        """The parse_version method must return Version(0, 0, -1)
                    if it gets digits only"""
        right_version = "2020124"

        # But it raises IndexError instead
        with pytest.raises(IndexError):
            _ = parse_version(right_version)

    def test_parse_version_right(self):
        """The parse_version method must return Version(2020, 12, 4)
                    if it gets 2020.12.4 as input"""
        right_version = "2020.12.4"
        parsed = parse_version(right_version)

        self.assertEqual(parsed.year, 2020)
        self.assertEqual(parsed.quart, 12)
        self.assertEqual(parsed.last, 4)

    def test_parse_version_short(self):
        """The parse_version method must return Version(2020, 12, -1)
                        if it gets 2020.12 as input"""
        right_version = "2020.12"
        parsed = parse_version(right_version)

        self.assertEqual(parsed.year, 2020)
        self.assertEqual(parsed.quart, 12)
        self.assertEqual(parsed.last, -1)

    def test_parse_version_incorrect(self):
        """The parse_version method must return Version(0, 0, -1)
                        if it gets incorrect_version as input"""
        incorrect_version = "incorrect_version"
        parsed = parse_version(incorrect_version)

        self.assertEqual(parsed.year, 0)
        self.assertEqual(parsed.quart, 0)
        self.assertEqual(parsed.last, -1)

    def test_parse_version_empty(self):
        """The parse_version method must return Version(0, 0, -1)
                        if it gets empty input"""
        empty_version = ""
        parsed = parse_version(empty_version)

        self.assertEqual(parsed.year, 0)
        self.assertEqual(parsed.quart, 0)
        self.assertEqual(parsed.last, -1)

    def test_get_data_dir_from_script(self):
        """The get_data_dir_from_script method must raise an exception
                        if it gets incorrect run script as input"""
        with pytest.raises(Exception):
            get_data_dir_from_script("incorrect_run_script")

    def test_is_mps_dir_false(self):
        """The is_mps_dir method must return false
                        if it gets incorrect mps dir as input"""
        self.assertFalse(is_mps_dir("is_not_mps_dir"))
