import os
import pytest

from unittest import TestCase
from ..config_generator import *


class ConfigGeneratorTest (TestCase):
    def test_token_quote(self):
        self.assertEqual(token_quote('some_token'), '\"some_token\"')