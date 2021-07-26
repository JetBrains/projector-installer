import os
import pytest

from unittest import TestCase
from ..apps import *


class AppsTest(TestCase):
    app_path = join(expanduser('~'), 'projector/apps/app_path')

    def test_get_app_path(self):
        user = expanduser('~')
        self.assertEqual(get_app_path("app_path"), f'{user}/.projector/apps/app_path')

    def test_is_path_to_app_false(self):
        self.assertFalse(is_path_to_app(self.app_path))

    # TODO: - Gives an error when version is a number, for example, 2020124
    # Is that normal? Can we get a version consisting of digits only?
    def test_parse_version_false(self):
        right_version = "2020124"

        with pytest.raises(IndexError):
            parsed = parse_version(right_version)

    def test_parse_version_right(self):
        right_version = "2020.12.4"
        parsed = parse_version(right_version)

        self.assertEqual(parsed.year, 2020)
        self.assertEqual(parsed.quart, 12)
        self.assertEqual(parsed.last, 4)

    def test_parse_version_short(self):
        right_version = "2020.12"
        parsed = parse_version(right_version)

        self.assertEqual(parsed.year, 2020)
        self.assertEqual(parsed.quart, 12)
        self.assertEqual(parsed.last, -1)

    def test_parse_version_wrong(self):
        wrong_version = "wrong_version"
        parsed = parse_version(wrong_version)

        self.assertEqual(parsed.year, 0)
        self.assertEqual(parsed.quart, 0)
        self.assertEqual(parsed.last, -1)

    def test_parse_version_empty(self):
        empty_version = ""
        parsed = parse_version(empty_version)

        self.assertEqual(parsed.year, 0)
        self.assertEqual(parsed.quart, 0)
        self.assertEqual(parsed.last, -1)

    def test_get_data_dir_from_script(self):
        with pytest.raises(Exception):
            get_data_dir_from_script("some_wrong_run_script")

    def test_is_mps_dir_false(self):
        self.assertFalse(is_mps_dir("is_not_mps_dir"))