#  GNU General Public License version 2
#
#  Copyright (C) 2019-2020 JetBrains s.r.o.
#
#  This program is free software; you can redistribute it and/or modify it
#  under the terms of the GNU General Public License version 2 only, as
#  published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program; if not, write to the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""
Global configuration constants, variables and functions.
"""

import json
import sys
from typing import List
from os.path import dirname, join, expanduser, abspath
from shutil import copyfile, rmtree
from .utils import download_file, get_file_name_from_url, unpack_zip_file, copy_all_files, \
    create_dir_if_not_exist

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
PLUGIN_DIR: str = 'plugin'
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


def get_lib_dir() -> str:
    """Returns full path to lib directory."""
    return join(config_dir, 'lib')


def get_compatible_ide_file() -> str:
    """Returns full path to compatible ide file."""
    return join(get_lib_dir(), COMPATIBLE_IDE_FILE)


COMPATIBLE_IDE_FILE_URL: str = \
    'https://raw.githubusercontent.com/JetBrains/projector-installer/master/compatible_ide.json'


def download_compatible_ide_file() -> None:
    """Downloads compatible ide json file from github repository."""
    download_file(COMPATIBLE_IDE_FILE_URL, get_download_cache_dir())
    name = get_file_name_from_url(COMPATIBLE_IDE_FILE_URL)
    source = join(get_download_cache_dir(), name)
    destination = join(get_lib_dir(), name)
    copyfile(source, destination)


def copy_compatible_ide_file() -> None:
    """Copy compatible ide file from module to lib dir."""
    source = join(INSTALL_DIR, COMPATIBLE_IDE_FILE)
    destination = join(get_lib_dir(), COMPATIBLE_IDE_FILE)
    copyfile(source, destination)


class CompatibleApp:
    """Compatible application entry."""

    def __init__(self, name: str, url: str) -> None:
        self.name: str = name
        self.url: str = url


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


def load_compatible_apps() -> None:
    """Loads compatible apps file to memory."""
    file_name = get_compatible_ide_file()

    with open(file_name, 'r') as file:
        data = json.load(file)

    for entry in data:
        app = CompatibleApp(entry['name'], entry['url'])
        COMPATIBLE_APPS.append(app)


def init_compatible_apps() -> None:
    """Initializes compatible apps list."""
    try:
        load_compatible_apps()
    except IOError:
        print('Cannot load compatible ide file, exiting...')
        sys.exit(2)


def get_http_dir() -> str:
    """Returns dir with client files."""
    return join(get_lib_dir(), 'client')


def get_projector_server_dir() -> str:
    """Returns directory with projector server jar"""
    return join(get_lib_dir(), 'server')


def get_projector_markdown_plugin_dir() -> str:
    """Returns directory with projector markdown plugin."""
    return join(get_lib_dir(), 'projector-markdown-plugin')


PROJECTOR_SERVER_URL: str = 'https://github.com/JetBrains/projector-server/releases/' \
                            'download/v0.0.1/projector-server-v0.0.1.zip'


def install_server() -> None:
    """Downloads and installs projector server"""
    download_file(PROJECTOR_SERVER_URL, get_download_cache_dir())
    file_path = join(get_download_cache_dir(), get_file_name_from_url(PROJECTOR_SERVER_URL))
    dir_name = unpack_zip_file(file_path, get_download_cache_dir())
    temp_dir = join(get_download_cache_dir(), dir_name)
    jars_path = join(temp_dir, 'lib')
    copy_all_files(jars_path, get_projector_server_dir())
    rmtree(temp_dir)


PROJECTOR_CLIENT_URL: str = 'https://github.com/JetBrains/projector-client/releases/' \
                            'download/v0.0.1/projector-client-web-distribution-v0.0.1.zip'


def install_client() -> None:
    """Downloads and installs projector client"""
    download_file(PROJECTOR_CLIENT_URL, get_download_cache_dir())
    file_path = join(get_download_cache_dir(), get_file_name_from_url(PROJECTOR_CLIENT_URL))
    unpack_zip_file(file_path, get_http_dir())


MARKDOWN_PLUGIN_URL: str = 'https://github.com/JetBrains/projector-markdown-plugin/releases/' \
                           'download/v0.0.1/projector-markdown-plugin-v0.0.1.zip'


def install_markdown_plugin() -> None:
    """Downloads and installs projector markdown plugin"""
    download_file(MARKDOWN_PLUGIN_URL, get_download_cache_dir())
    file_path = join(get_download_cache_dir(), get_file_name_from_url(MARKDOWN_PLUGIN_URL))
    unpack_zip_file(file_path, get_lib_dir())


def init_lib_dir() -> None:
    """Initializes lib directory."""
    # pylint: disable=W0703
    try:
        create_dir_if_not_exist(get_lib_dir())
        create_dir_if_not_exist(get_http_dir())
        create_dir_if_not_exist(get_projector_server_dir())
        create_dir_if_not_exist(get_projector_markdown_plugin_dir())
        # download_compatible_ide_file()
        copy_compatible_ide_file()
        install_server()
        install_client()
        install_markdown_plugin()
    except Exception as exception:
        print(f'Error during initialization: {str(exception)}, cleanup ...')
        rmtree(get_lib_dir())
        sys.exit(1)


def init_config_dir() -> None:
    """Initializes global config directory."""
    # pylint: disable=W0703
    try:
        create_dir_if_not_exist(config_dir)
        create_dir_if_not_exist(get_apps_dir())
        create_dir_if_not_exist(get_run_configs_dir())
        create_dir_if_not_exist(get_download_cache_dir())
        init_lib_dir()
        init_compatible_apps()
    except Exception as exception:
        print(f'Error during initialization: {str(exception)}, cleanup ...')
        rmtree(config_dir)
        sys.exit(1)
