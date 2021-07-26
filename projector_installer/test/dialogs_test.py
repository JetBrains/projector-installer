import os
import io
import pytest

from unittest import TestCase
from unittest import mock
from unittest.mock import patch

from ..dialogs import *


class DialogsTests(TestCase):
    def test_get_user_input(self):
        some_input = 'some_input'
        original_input = mock.builtins.input
        mock.builtins.input = lambda _: some_input
        self.assertEqual(get_user_input('prompt', 'default'), some_input)
        mock.builtins.input = original_input

    def test_get_user_input_default(self):
        original_input = mock.builtins.input
        mock.builtins.input = lambda _: ''
        self.assertEqual(get_user_input('prompt', 'default'), 'default')
        mock.builtins.input = original_input

    def test_is_boolean_input_true(self):
        self.assertTrue(is_boolean_input('Y'))
        self.assertTrue(is_boolean_input('y'))
        self.assertTrue(is_boolean_input('N'))
        self.assertTrue(is_boolean_input('n'))

    def test_is_boolean_input_false(self):
        self.assertFalse(is_boolean_input('123'))
        self.assertFalse(is_boolean_input('true'))

    def test_ask_yes(self):
        original_input = mock.builtins.input
        mock.builtins.input = lambda _: 'y'
        self.assertTrue(ask('prompt', True))
        mock.builtins.input = original_input

    def test_ask_no(self):
        original_input = mock.builtins.input
        mock.builtins.input = lambda _: 'n'
        self.assertFalse(ask('prompt', False))
        mock.builtins.input = original_input

    def test_ask_empty(self):
        original_input = mock.builtins.input
        mock.builtins.input = lambda _: ''
        self.assertTrue(ask('prompt', True))
        mock.builtins.input = original_input

    def test_prompt_with_default(self):
        some_input = 'non empty input'
        original_input = mock.builtins.input
        mock.builtins.input = lambda _: some_input
        self.assertEqual(prompt_with_default(prompt='prompt', default='default'), some_input)
        mock.builtins.input = original_input

    def test_prompt_with_default_empty_input(self):
        empty_input = ''
        original_input = mock.builtins.input
        mock.builtins.input = lambda _: empty_input
        self.assertEqual(prompt_with_default(prompt='prompt', default='default'), 'default')
        mock.builtins.input = original_input

    def test_get_all_listening_ports(self):
        if platform.system() != 'Linux':
            self.assertEqual(get_all_listening_ports(), [])