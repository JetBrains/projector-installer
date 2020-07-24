# Copyright 2000-2020 JetBrains s.r.o.
# Use of this source code is governed by the Apache 2.0 license that can be found
# in the LICENSE file.


"""
Global configuration constants, variables and functions.
"""

import json
import sys
from typing import List
from shutil import rmtree
from socket import timeout
from os.path import dirname, join, expanduser, abspath

from .utils import create_dir_if_not_exist, download_file, get_file_name_from_url

USER_HOME: str = expanduser('~')
INSTALL_DIR: str = dirname(abspath(__file__))
DEF_HTTP_PORT: int = 8889
DEF_PROJECTOR_PORT: int = 9999
COMPATIBLE_IDE_FILE: str = 'compatible_ide.json'
PROJECTOR_LOG_FILE: str = 'projector.log'
DEF_CONFIG_DIR: str = '.projector'
BUNDLED_DIR: str = 'bundled'
SERVER_DIR: str = 'server'
CLIENT_DIR: str = 'client'
PLUGIN_DIR: str = 'projector-markdown-plugin'
config_dir: str = join(USER_HOME, DEF_CONFIG_DIR)


def get_path_to_license() -> str:
    """Returns full path to license file"""
    return join(INSTALL_DIR, 'LICENSE.txt')


def get_path_to_projector_log() -> str:
    """Returns full path to projector log file"""
    return join(config_dir, PROJECTOR_LOG_FILE)


def get_apps_dir() -> str:
    """Returns full path to applications directory."""
    return join(config_dir, 'apps')


def get_run_configs_dir() -> str:
    """Returns full path to run configs directory."""
    return join(config_dir, 'configs')


def get_download_cache_dir() -> str:
    """Returns full path to download cache directory."""
    return join(config_dir, 'cache')


def get_compatible_ide_file() -> str:
    """Returns full path to compatible ide file."""
    return join(INSTALL_DIR, COMPATIBLE_IDE_FILE)


class CompatibleApp:
    """Compatible application entry."""

    def __init__(self, name: str, url: str) -> None:
        self.name: str = name
        self.url: str = url

    def __eq__(self, other: object) -> bool:
        if isinstance(other, CompatibleApp):
            return self.name == other.name and self.url == other.url

        return False


COMPATIBLE_APPS: List[CompatibleApp] = []


class RunConfig:
    """Run config dataclass"""

    def __init__(self, path_to_app: str, ide_config_dir: str, projector_port: int,
                 http_address: str, http_port: int) -> None:
        self.path_to_app: str = path_to_app
        self.ide_config_dir: str = ide_config_dir
        self.projector_port: int = projector_port
        self.http_address: str = http_address
        self.http_port: int = http_port


def load_compatible_apps_from_file(file_name: str) -> None:
    """Loads compatible apps file to memory."""
    with open(file_name, 'r') as file:
        data = json.load(file)

    for entry in data:
        app = CompatibleApp(entry['name'], entry['url'])
        if app not in COMPATIBLE_APPS:
            COMPATIBLE_APPS.append(app)


COMPATIBLE_IDE_FILE_URL: str = \
    'https://raw.githubusercontent.com/JetBrains/projector-installer/master/' \
    'projector_installer/compatible_ide.json'


def download_compatible_apps() -> str:
    """Downloads compatible ide json file from github repository."""
    try:
        download_file(COMPATIBLE_IDE_FILE_URL, get_download_cache_dir(), timeout=3, silent=True)
        name = get_file_name_from_url(COMPATIBLE_IDE_FILE_URL)
        file_name = join(get_download_cache_dir(), name)

        return file_name
    except timeout:
        return ''


def load_compatible_apps() -> None:
    """Loads compatible apps dictionary from bundled file and github-stored Json"""
    file_name = get_compatible_ide_file()
    load_compatible_apps_from_file(file_name)
    github_file = download_compatible_apps()

    if github_file:
        load_compatible_apps_from_file(github_file)


def init_compatible_apps() -> None:
    """Initializes compatible apps list."""
    try:
        load_compatible_apps()
    except IOError as error:
        print(f'Cannot load compatible ide file: {str(error)}. Exiting...')
        sys.exit(2)


def get_http_dir() -> str:
    """Returns dir with client files."""
    return join(INSTALL_DIR, BUNDLED_DIR, CLIENT_DIR)


def get_projector_server_dir() -> str:
    """Returns directory with projector server jar"""
    return join(INSTALL_DIR, BUNDLED_DIR, SERVER_DIR)


def get_projector_markdown_plugin_dir() -> str:
    """Returns directory with projector markdown plugin."""
    return join(INSTALL_DIR, BUNDLED_DIR, PLUGIN_DIR)


def init_config_dir() -> None:
    """Initializes global config directory."""
    # pylint: disable=W0703
    try:
        create_dir_if_not_exist(config_dir)
        create_dir_if_not_exist(get_apps_dir())
        create_dir_if_not_exist(get_run_configs_dir())
        create_dir_if_not_exist(get_download_cache_dir())
        init_compatible_apps()
    except Exception as exception:
        print(f'Error during initialization: {str(exception)}, cleanup ...')
        rmtree(config_dir)
        sys.exit(1)
