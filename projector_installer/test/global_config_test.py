import os
import pytest

from unittest import TestCase
from ..global_config import *


class GlobalConfigTest(TestCase):
    user = expanduser('~')

    def test_get_changelog_url(self):
        changelog_url = f'https://github.com/JetBrains/projector-installer/blob/master/CHANGELOG.md#2020131'
        self.assertEqual(get_changelog_url(ver='2020.13.1'), changelog_url)

    def test_get_path_to_license(self):
        path_to_license = f'{self.user}/PycharmProjects/projector-installer/projector_installer/LICENSE.txt'
        self.assertEqual(get_path_to_license(), path_to_license)

    def test_get_apps_dir(self):
        apps_dir = f'{self.user}/.projector/apps'
        self.assertEqual(get_apps_dir(), apps_dir)

    def test_get_run_configs_dir(self):
        run_configs_dir = f'{self.user}/.projector/configs'
        self.assertEqual(get_run_configs_dir(), run_configs_dir)

    def test_get_ssl_properties_file(self):
        config_name = 'config_name'
        ssl_properties_file = f'{self.user}/.projector/configs/{config_name}/ssl.properties'
        self.assertEqual(get_ssl_properties_file(config_name=config_name), ssl_properties_file)

    def test_get_download_cache_dir(self):
        download_cache_dir = f'{self.user}/.projector/cache'
        self.assertEqual(download_cache_dir, get_download_cache_dir())

    def test_get_ssl_dir(self):
        ssl_dir = f'{self.user}/.projector/ssl'
        self.assertEqual(get_ssl_dir(), ssl_dir)

    def test_get_projector_server_dir(self):
        projector_server_dir = f'{self.user}/PycharmProjects/projector-installer/projector_installer/bundled/server'
        self.assertEqual(get_projector_server_dir(), projector_server_dir)
