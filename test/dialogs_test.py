"""Test dialogs.py module"""
from unittest import TestCase
from unittest import mock

import sys
import pytest

from projector_installer.dialogs import get_user_input, is_boolean_input, ask, \
    prompt_with_default, get_all_listening_ports


class DialogsTests(TestCase):
    """Test dialogs.py module"""

    def test_get_user_input(self):  # type: ignore
        """The get_user_input method must return the user's input"""
        some_input = 'some_input'
        original_input = mock.builtins.input
        mock.builtins.input = lambda _: some_input
        self.assertEqual(get_user_input('prompt', 'default'), some_input)
        mock.builtins.input = original_input

    def test_get_user_input_default(self):  # type: ignore
        """The get_user_input method must return default if the input is empty"""
        original_input = mock.builtins.input
        mock.builtins.input = lambda _: ''
        self.assertEqual(get_user_input('prompt', 'default'), 'default')
        mock.builtins.input = original_input

    def test_is_boolean_input_true(self):  # type: ignore
        """
        The is_boolean_input method must return true
        if the user's input is in ['Y', 'y', 'N', 'n']
        """
        self.assertTrue(is_boolean_input('Y'))
        self.assertTrue(is_boolean_input('y'))
        self.assertTrue(is_boolean_input('N'))
        self.assertTrue(is_boolean_input('n'))

    def test_is_boolean_input_false(self):  # type: ignore
        """
        The is_boolean_input method must return false
        if the user's input is not in ['Y', 'y', 'N', 'n']
        """
        self.assertFalse(is_boolean_input('123'))
        self.assertFalse(is_boolean_input('true'))
        self.assertFalse(is_boolean_input(''))

    def test_ask_yes(self):  # type: ignore
        """The ask method must return true if the user's input is 'y'"""
        original_input = mock.builtins.input
        mock.builtins.input = lambda _: 'y'
        self.assertTrue(ask('prompt', True))
        mock.builtins.input = original_input

    def test_ask_no(self):  # type: ignore
        """The ask method must return false if the user's input is 'n'"""
        original_input = mock.builtins.input
        mock.builtins.input = lambda _: 'n'
        self.assertFalse(ask('prompt', False))
        mock.builtins.input = original_input

    def test_ask_empty(self):  # type: ignore
        """The ask method must return true if the user's input is empty"""
        original_input = mock.builtins.input
        mock.builtins.input = lambda _: ''
        self.assertTrue(ask('prompt', True))
        mock.builtins.input = original_input

    def test_prompt_with_default(self):  # type: ignore
        """The prompt_with_default method must return the user's input"""
        some_input = 'non empty input'
        original_input = mock.builtins.input
        mock.builtins.input = lambda _: some_input
        self.assertEqual(prompt_with_default(prompt='prompt', default='default'), some_input)
        mock.builtins.input = original_input

    def test_prompt_with_default_empty_input(self):  # type: ignore
        """The prompt_with_default method must return 'default' if the user's input is empty"""
        empty_input = ''
        original_input = mock.builtins.input
        mock.builtins.input = lambda _: empty_input
        self.assertEqual(prompt_with_default(prompt='prompt', default='default'), 'default')
        mock.builtins.input = original_input

    @pytest.mark.skipif(sys.platform == "linux", reason="test for non-linux only")
    def test_get_all_listening_ports(self) -> None:
        """
        The get_all_listening_ports method must return an empty array
        if the platform is not Linux
        """
        self.assertEqual(get_all_listening_ports(), [])
