# Copyright 2000-2020 JetBrains s.r.o.
# Use of this source code is governed by the Apache 2.0 license that can be found
# in the LICENSE file.


"""Application management functions."""
import sys
from os import listdir, rename
from os.path import join, expanduser, dirname, isfile, isdir, basename
from distutils.version import LooseVersion
from typing import Optional, List
from dataclasses import dataclass
import json

from .global_config import get_apps_dir, get_download_cache_dir
from .utils import unpack_tar_file, expand_path, download_file, create_dir_if_not_exist

IDEA_PATH_SELECTOR = 'idea.paths.selector'


def get_installed_apps(pattern: Optional[str] = None) -> List[str]:
    """Returns sorted list of installed apps, matched given pattern."""
    res = [file_name for file_name in listdir(get_apps_dir()) if
           pattern is None or file_name.lower().find(pattern.lower()) != -1]
    res.sort()
    return res


def get_app_path(app_name: str) -> str:
    """Returns full path to given app."""
    return join(get_apps_dir(), app_name)


@dataclass
class ProductInfo:
    """Ide product info"""

    # pylint: disable=too-many-instance-attributes
    name: str
    version: str
    build_number: str
    product_code: str
    data_dir: str
    svg_icon_path: str
    os: str
    launcher_path: str
    java_exec_path: str
    vm_options_path: str
    startup_wm_class: str


PRODUCT_INFO = 'product-info.json'


class Version:
    """Three-parts version representation."""

    def __init__(self, year: int, quart: int, last: int):
        self.year: int = year
        self.quart: int = quart
        self.last: int = last


def parse_version(version: str) -> Version:
    """Parses version string to Version class."""
    parsed = version.split(".")

    try:
        return Version(int(parsed[0]), int(parsed[1]), int(parsed[2] if len(parsed) > 2 else -1))
    except ValueError:
        return Version(0, 0, -1)


def get_data_dir_from_script(run_script: str) -> str:
    """Returns idea data dir from run script."""
    with open(run_script, 'r') as file:
        for line in file:
            pos = line.find(IDEA_PATH_SELECTOR)

            if pos != -1:
                parts = line.split('=')

                if len(parts) < 2:
                    raise Exception(f'Unable to parse {IDEA_PATH_SELECTOR} line.')

                return parts[1].split(' ')[0]

    raise Exception('Unable to find data directory in the launch script.')


def get_product_info(app_path: str) -> ProductInfo:
    """Parses product info file to ProductInfo class."""
    prod_info_path = join(app_path, PRODUCT_INFO)
    with open(prod_info_path, "r") as file:
        data = json.load(file)
        java_exec_path = 'jre/bin/java'

        if 'javaExecutablePath' in data['launch'][0]:
            java_exec_path = data['launch'][0]['javaExecutablePath']

        product_info = ProductInfo(data['name'], data['version'], data['buildNumber'],
                                   data['productCode'], '', data['svgIconPath'],
                                   data['launch'][0]['os'],
                                   data['launch'][0]['launcherPath'],
                                   java_exec_path,
                                   data['launch'][0]['vmOptionsFilePath'],
                                   data['launch'][0]['startupWmClass'])

        version = parse_version(product_info.version)

        if version.year >= 2020 and version.quart >= 2:
            product_info.data_dir = data['dataDirectoryName']
        else:
            product_info.data_dir = get_data_dir_from_script(
                join(app_path, product_info.launcher_path))

        return product_info


def get_launch_script(app_path: str) -> str:
    """Returns full path to launch script by ide path."""
    prod_info = get_product_info(app_path)
    return join(app_path, prod_info.launcher_path)


def get_bin_dir(app_path: str) -> str:
    """Get full path to ide bin dir."""
    run_script = get_launch_script(app_path)
    return dirname(run_script)


CONFIG_PREFIX = expanduser('~/')
VER_2020_CONFIG_PREFIX = expanduser('~/.config/JetBrains')
ANDROID_STUDIO_CONFIG_PREFIX = expanduser('~/.config/Google')


def get_config_dir(app_path: str) -> str:
    """Returns ide config directory."""
    product_info = get_product_info(app_path)
    version = parse_version(product_info.version)

    if is_android_studio(product_info):
        return join(ANDROID_STUDIO_CONFIG_PREFIX, product_info.data_dir)

    if version.year >= 2020:
        return join(VER_2020_CONFIG_PREFIX, product_info.data_dir)

    return join(join(CONFIG_PREFIX, '.' + product_info.data_dir), 'config')


PLUGIN_2020_PREFIX: str = expanduser('~/.local/share/JetBrains')
ANDROID_STUDIO_PLUGIN_PREFIX = expanduser('~/.local/share/Google')


def get_plugin_dir(app_path: str) -> str:
    """Returns full path to application plugin directory."""
    product_info = get_product_info(app_path)
    version = parse_version(product_info.version)

    if is_android_studio(product_info):
        return join(ANDROID_STUDIO_PLUGIN_PREFIX, product_info.data_dir)

    if version.year >= 2020:
        return join(PLUGIN_2020_PREFIX, product_info.data_dir)

    return join(get_config_dir(app_path), "plugins")


def is_android_studio(product_info: ProductInfo) -> bool:
    """Returns True if given product info corresponds to is from AS"""
    return product_info.product_code == 'AI'


def get_java_path(app_path: str) -> str:
    """Returns full path to bundled java."""
    product_info = get_product_info(app_path)
    return join(app_path, product_info.java_exec_path)


def unpack_app(file_path: str) -> str:
    """Unpacks specified file to app directory."""
    app_name = unpack_tar_file(file_path, get_apps_dir())

    # For android studio - ensure that app directory has unique name
    app_path = get_app_path(app_name)
    product_info = get_product_info(app_path)

    if is_android_studio(product_info):
        versioned_name = app_name + "_" + product_info.version.replace(' ', '_')
        new_path = get_app_path(versioned_name)
        rename(app_path, new_path)
        app_name = versioned_name

    return app_name


def get_jre_dir(path_to_app: str) -> str:
    """Return path to dir with bundled jre"""
    product_info = get_product_info(path_to_app)

    if is_android_studio(product_info):
        return join(path_to_app, 'jre')

    return join(path_to_app, 'jbr')


def is_path_to_app(app_path: str) -> bool:
    """Checks app path validity"""
    prod_info_path = join(app_path, PRODUCT_INFO)
    return isfile(prod_info_path)


def get_path_to_toolbox_channel(path: str) -> Optional[str]:
    """"Returns path to toolbox channel"""
    pos = path.find('JetBrains/Toolbox/apps')

    if pos >= 0:
        ch_path = path.rstrip('/')
        ch_pos = ch_path.find('ch-')

        if ch_pos > pos:
            sep_pos = ch_path.find('/', ch_pos + 1)

            if sep_pos < 0:
                return ch_path

            return ch_path[:sep_pos]

    return None


def is_toolbox_path(app_path: str) -> bool:
    """Checks if given path is toolbox channel path"""
    return get_path_to_toolbox_channel(app_path) is not None


def is_valid_app_path(app_path: str) -> bool:
    """Checks if entered app path is valid"""
    return is_path_to_app(app_path) or is_toolbox_path(app_path)


def get_path_to_latest_app(path: str) -> Optional[str]:
    """Returns path to the app with latest version in channel"""
    channel_path = get_path_to_toolbox_channel(path)

    if channel_path is None:
        return None

    app_path = None
    app_ver = None

    for sub_dir in listdir(channel_path):
        app_dir = join(channel_path, sub_dir)

        if isdir(app_dir) and is_path_to_app(app_dir):
            ver = LooseVersion(get_product_info(app_dir).version)

            if app_path is None or app_ver < ver:
                app_path = app_dir
                app_ver = ver

    return app_path


def get_product_name(app_path: str) -> str:
    """Returns name from product info file by app path"""
    info = get_product_info(app_path)
    return info.name.replace(' ', '_')


def get_app_name_from_toolbox_path(toolbox_path: str) -> str:
    """Returns app name by toolbox path"""
    app_path = get_path_to_latest_app(toolbox_path)

    if app_path is None:
        raise ValueError(f'Invalid path to toolbox app: {toolbox_path}')

    return get_product_name(app_path)


def get_channel_from_toolbox_path(toolbox_channel_path: str) -> str:
    """Returns channel name by toolbox path"""
    return basename(toolbox_channel_path)


def is_projector_installed_ide(path_to_ide: str) -> bool:
    """Returns True if IDE is installed """
    ide_path = expand_path(path_to_ide)
    return ide_path.startswith(get_apps_dir())


def is_disabled(file_name: str, plugin_name: str) -> bool:
    """Checks if given plugin is already disabled"""
    if not isfile(file_name):
        return False

    with open(file_name, 'r') as file:
        lines = [line.strip() for line in file]
        return plugin_name in lines


def disable_plugin(file_name: str, plugin_name: str) -> None:
    """Disables specified plugin"""
    directory = dirname(file_name)
    create_dir_if_not_exist(directory)

    with open(file_name, 'a') as file:
        file.write(f'{plugin_name}')


DISABLED_PLUGINS_FILE = 'disabled_plugins.txt'
IDEA_PROPERTIES_FILE = 'idea.properties'
FORBID_UPDATE_STRING = 'ide.no.platform.update=Projector'


def forbid_updates_for(app_path: str) -> None:
    """Forbids IDEA platform update for specified app."""
    bin_dir = get_bin_dir(app_path)
    prop_file = join(bin_dir, IDEA_PROPERTIES_FILE)

    with open(prop_file, 'a') as file:
        file.write(f'{FORBID_UPDATE_STRING}')


def download_and_install(url: str, allow_updates: bool) -> str:
    """Downloads and installs app"""
    try:
        path_to_dist = download_file(url, get_download_cache_dir())
    except IOError as error:
        print(f'Unable to write downloaded file, try again later: {str(error)}. Exiting ...')
        sys.exit(1)

    try:
        app_name = unpack_app(path_to_dist)
    except IOError as error:
        print(f'Unable to extract the archive: {str(error)}, exiting...')
        sys.exit(1)

    res = get_app_path(app_name)

    if not allow_updates:
        forbid_updates_for(res)

    return res
