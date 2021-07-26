import os
import pytest

from unittest import TestCase
from ..log_utils import *


class LogUtilsTest(TestCase):
    def test_is_unexpected_exit(self):
        self.assertTrue(is_unexpected_exit(ret_code=1))
        self.assertFalse(is_unexpected_exit(ret_code=0))
        self.assertFalse(is_unexpected_exit(ret_code=-2))
        self.assertFalse(is_unexpected_exit(ret_code=-15))
