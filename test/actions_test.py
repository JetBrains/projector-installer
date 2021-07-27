"""Test actions.py module"""
from unittest import TestCase
import pytest

from projector_installer.actions import is_compatible_java


class ActionsTest(TestCase):
    """Test actions.py module"""

    def test_is_compatible_java_false(self):
        """The is_compatible_java method must raise an exception
        if the input app path is incorrect"""
        with pytest.raises(Exception):
            is_compatible_java("incorrect_app_path")
