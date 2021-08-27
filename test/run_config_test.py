"""Test run_config.py module"""
from os.path import expanduser
import os

from unittest import TestCase
import pytest

from projector_installer.run_config import get_path_to_config, get_path_to_certificate_dir, \
    get_run_script_path, make_config_name, RunConfig, validate_run_config, \
    get_lock_file_name, lock_config
from projector_installer.version import __version__


class RunConfigTest(TestCase):
    """Test run_config.py module"""

    user = expanduser('~')

    def test_get_path_to_config(self) -> None:
        """The get_path_to_config method must return path to config with a given name"""
        config_name = 'config_name'
        path_to_config = f'{self.user}/.projector/configs/{config_name}'
        self.assertEqual(get_path_to_config(config_name), path_to_config)

    def test_get_path_to_certificate_dir(self) -> None:
        """
        The get_path_to_certificate_dir method must return path to certificate dir of given config
        """
        config_name = 'config_name'
        path_to_certificate_dir = f'{self.user}/.projector/configs/{config_name}/cert'
        self.assertEqual(get_path_to_certificate_dir(config_name), path_to_certificate_dir)

    def test_get_run_script_path(self) -> None:
        """The get_run_script_path method must return path to run script of given config name"""
        config_name = 'config_name'
        run_script_path = f'{self.user}/.projector/configs/{config_name}/run.sh'
        self.assertEqual(get_run_script_path(config_name), run_script_path)

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

    def test_validate_run_config_no_errors(self) -> None:
        """The validate_run_config method must not raise error when run config is valid"""
        app_dir_path = f'{self.user}/.projector/apps/app_dir'
        os.makedirs(app_dir_path)

        run_config = RunConfig(name='name', path_to_app=app_dir_path, projector_port=8887,
                               token='token', password='password', ro_password='ro_password',
                               toolbox=True, custom_names='custom_names')

        validate_run_config(run_config)
        os.removedirs(app_dir_path)

    def test_validate_run_config_raises_error(self) -> None:
        """The validate_run_config method must raise error when path to app is invalid"""
        run_config = RunConfig(name='name', path_to_app='path_to_app', projector_port=8887,
                               token='token', password='password', ro_password='ro_password',
                               toolbox=True, custom_names='custom_names')

        with pytest.raises(ValueError):
            validate_run_config(run_config)

    def test_get_lock_file_name(self) -> None:
        """The get_lock_file_name method must return a path to lock file for given config name"""
        config_name = 'config_name'
        lock_file_name = f'{self.user}/.projector/configs/{config_name}/run.lock'
        self.assertEqual(get_lock_file_name(config_name), lock_file_name)

    def test_lock_config(self) -> None:
        """The lock_config method must return the TextIO of file if lock was successful"""
        config_name = 'config_name'
        config_dir_path = f'{self.user}/.projector/configs/{config_name}'
        os.makedirs(config_dir_path)

        lock_file_path = f'{config_dir_path}/run.lock'
        open(lock_file_path, 'w', encoding="utf-8").close()
        output = lock_config(config_name)

        expected_output = f"<_io.TextIOWrapper name='{self.user}/.projector/configs/" \
                          f"config_name/run.lock' mode='w' encoding='utf-8'>"
        self.assertEqual(str(output), expected_output)

        os.remove(lock_file_path)
        os.removedirs(config_dir_path)
