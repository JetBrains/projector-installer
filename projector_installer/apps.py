# Copyright 2000-2020 JetBrains s.r.o.
# Use of this source code is governed by the Apache 2.0 license that can be found
# in the LICENSE file.


"""Application management functions."""

from os.path import join, expanduser, dirname
from os import listdir, chmod, stat
from typing import Optional, List
import json

from .global_config import get_apps_dir, get_projector_server_dir, COMPATIBLE_APPS, \
    CompatibleApp, RunConfig
from .utils import unpack_tar_file

IDEA_RUN_CLASS = 'com.intellij.idea.Main'
PROJECTOR_RUN_CLASS = 'org.jetbrains.projector.server.ProjectorLauncher'
IDEA_PLATFORM_PREFIX = 'idea.platform.prefix'
IDEA_PATH_SELECTOR = 'idea.paths.selector'


def unpack_app(file_path: str) -> str:
    """Unpacks specified file to app directory."""
    return unpack_tar_file(file_path, get_apps_dir())


def get_installed_apps(pattern: Optional[str] = None) -> List[str]:
    """Returns sorted list of installed apps, matched given pattern."""
    res = [file_name for file_name in listdir(get_apps_dir()) if
           pattern is None or file_name.lower().find(pattern.lower()) != -1]
    res.sort()
    return res


def get_compatible_apps(pattern: Optional[str] = None) -> List[CompatibleApp]:
    """Returns list of compatible apps, matched given pattern."""
    apps = [app for app in COMPATIBLE_APPS if
            pattern is None or app.name.lower().find(pattern.lower()) != -1]

    if pattern:
        for app in apps:
            if pattern.lower() == app.name.lower():
                return [app]

    return apps


def get_compatible_app_names(pattern: Optional[str] = None) -> List[str]:
    """Get sorted list of projector-compatible applications, matches given pattern."""
    res = [app.name for app in get_compatible_apps(pattern)]
    res.sort()
    return res


def get_app_path(app_name: str) -> str:
    """Returns full path to given app."""
    return join(get_apps_dir(), app_name)


def make_run_script(run_config: RunConfig, run_script: str) -> None:
    """Creates run script from ide launch script."""
    idea_script = get_launch_script(run_config.path_to_app)

    with open(idea_script, 'r') as src, open(run_script, 'w') as dst:
        for line in src:
            if line.startswith("IDE_BIN_HOME"):
                line = f'IDE_BIN_HOME={join(run_config.path_to_app, "bin")}\n'
            elif line.find("classpath") != -1:
                line = f'  -classpath "$CLASSPATH:{get_projector_server_dir()}/*" \\\n'
            elif line.find(IDEA_PATH_SELECTOR) != -1:
                if run_config.ide_config_dir:
                    line = f'  -D{IDEA_PATH_SELECTOR}={run_config.ide_config_dir} \\\n'
            elif line.find(IDEA_RUN_CLASS) != -1:
                line = f'  -Dorg.jetbrains.projector.server.port={run_config.projector_port} \\\n'
                line += f'  -Dorg.jetbrains.projector.server.classToLaunch={IDEA_RUN_CLASS} \\\n'
                line += f'  {PROJECTOR_RUN_CLASS}\\\n'

            dst.write(line)

    stats = stat(run_script)
    chmod(run_script, stats.st_mode | 0o0111)


class ProductInfo:
    """Ide product info"""

    # pylint: disable=too-many-instance-attributes
    def __init__(self, name: str, version: str, build_number: str, product_code: str,
                 data_dir: str, svg_icon_path: str, os: str, launcher_path: str,
                 java_exec_path: str, vm_options_path: str, startup_wm_class: str) -> None:
        self.name: str = name
        self.version: str = version
        self.build_number: str = build_number
        self.product_code: str = product_code
        self.data_dir: str = data_dir
        self.svg_icon_path: str = svg_icon_path
        self.os: str = os
        self.launcher_path: str = launcher_path
        self.java_exec_path: str = java_exec_path
        self.vm_options_path: str = vm_options_path
        self.startup_wm_class: str = startup_wm_class


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
    return Version(int(parsed[0]), int(parsed[1]), int(parsed[2] if len(parsed) > 2 else -1))


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

        product_info = ProductInfo(data['name'], data['version'], data['buildNumber'],
                                   data['productCode'], '', data['svgIconPath'],
                                   data['launch'][0]['os'],
                                   data['launch'][0]['launcherPath'],
                                   data['launch'][0]['javaExecutablePath'],
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


def get_config_dir(app_path: str) -> str:
    """Returns ide config directory."""
    product_info = get_product_info(app_path)
    version = parse_version(product_info.version)

    if version.year >= 2020:
        return join(VER_2020_CONFIG_PREFIX, product_info.data_dir)

    return join(join(CONFIG_PREFIX, '.' + product_info.data_dir), 'config')


PLUGIN_2020_PREFIX: str = expanduser('~/.local/share/JetBrains')


def get_plugin_dir(app_path: str) -> str:
    """Returns full path to application plugin directory."""
    product_info = get_product_info(app_path)
    version = parse_version(product_info.version)

    if version.year >= 2020:
        return join(PLUGIN_2020_PREFIX, product_info.data_dir)

    return join(get_config_dir(app_path), "plugins")
