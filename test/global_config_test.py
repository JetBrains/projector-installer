"""Test global_config.py module"""
from unittest import TestCase
from os.path import expanduser

from projector_installer.global_config import get_changelog_url, \
    get_apps_dir, get_run_configs_dir, get_ssl_properties_file, \
    get_download_cache_dir, get_ssl_dir


class GlobalConfigTest(TestCase):
    """Test global_config.py module"""

    user = expanduser('~')

    def test_get_changelog_url(self) -> None:
        """The get_changelog_url method must return changelog url with the specified version"""
        changelog_url = 'https://github.com/JetBrains/projector-installer' \
                        '/blob/master/CHANGELOG.md#2020131'
        self.assertEqual(get_changelog_url(ver='2020.13.1'), changelog_url)

    def test_get_apps_dir(self) -> None:
        """The get_apps_dir method must return full path to apps' directory"""
        apps_dir = f'{self.user}/.projector/apps'
        self.assertEqual(get_apps_dir(), apps_dir)

    def test_get_run_configs_dir(self) -> None:
        """The get_run_configs_dir method must return full path to configs"""
        run_configs_dir = f'{self.user}/.projector/configs'
        self.assertEqual(get_run_configs_dir(), run_configs_dir)

    def test_get_ssl_properties_file(self) -> None:
        """
        The get_ssl_properties_file method must return full path
        to ssl.properties file with the specified config name
        """
        config_name = 'config_name'
        ssl_properties_file = f'{self.user}/.projector/configs/{config_name}/ssl.properties'
        self.assertEqual(get_ssl_properties_file(config_name=config_name), ssl_properties_file)

    def test_get_download_cache_dir(self) -> None:
        """The download_cache_dir method must return full path to cache's directory"""
        download_cache_dir = f'{self.user}/.projector/cache'
        self.assertEqual(download_cache_dir, get_download_cache_dir())

    def test_get_ssl_dir(self) -> None:
        """The get_ssl_dir method must return full path to ssl's directory"""
        ssl_dir = f'{self.user}/.projector/ssl'
        self.assertEqual(get_ssl_dir(), ssl_dir)
