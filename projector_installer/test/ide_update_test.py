import os
import pytest

from unittest import TestCase
from ..ide_update import *


class IdeUpdateTest(TestCase):
    def test_is_updatable_ide_false(self):
        self.assertFalse(is_updatable_ide(path_to_ide='some_wrong_path'))