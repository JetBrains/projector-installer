import os
import pytest

from unittest import TestCase
from ..actions import *


class ActionsTest(TestCase):
    def test_is_compatible_java_false(self):
        with pytest.raises(Exception):
            self.assertFalse(is_compatible_java("some_wrong_path"))

    def test_is_wsl_false(self):
        self.assertFalse(is_wsl())