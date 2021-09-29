"""Test run_config.py module"""

from unittest import TestCase
import pytest

from projector_installer.run_config import make_config_name, RunConfig, validate_run_config


class RunConfigTest(TestCase):
    """Test run_config.py module"""

    def test_make_config_name(self) -> None:
        """
        The make_config_name method must return the same app name as provided if there is no space
        """
        app_name = 'app_name'
        self.assertEqual(make_config_name(app_name), 'app_name')

    def test_make_config_name_with_space(self) -> None:
        """The make_config_name method must return the first part of app name when name has space"""
        app_name = 'app name'
        self.assertEqual(make_config_name(app_name), 'app')

    def test_validate_run_config_raises_error(self) -> None:
        """The validate_run_config method must raise error when path to app is invalid"""
        run_config = RunConfig(name='name', path_to_app='path_to_app',
                               use_separate_config=False,
                               projector_port=8887,
                               token='token', password='password', ro_password='ro_password',
                               toolbox=True, custom_names='custom_names')

        with pytest.raises(ValueError):
            validate_run_config(run_config)
