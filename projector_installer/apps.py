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

from dataclasses import dataclass
from os.path import join, expanduser, dirname
from os import listdir, chmod, stat
import json
from .global_config import get_apps_dir, PROJECTOR_SERVER_DIR, COMPATIBLE_APPS
from .utils import unpack_tar_file

IDEA_RUN_CLASS = 'com.intellij.idea.Main'
PROJECTOR_RUN_CLASS = 'org.jetbrains.projector.server.ProjectorLauncher'
IDEA_PLATFORM_PREFIX = 'idea.platform.prefix'
IDEA_PATH_SELECTOR = 'idea.paths.selector'


def unpack_app(file_path):
    return unpack_tar_file(file_path, get_apps_dir())


def get_installed_apps(pattern=None):
    res = [file_name for file_name in listdir(get_apps_dir()) if
           pattern is None or file_name.lower().find(pattern.lower()) != -1]
    res.sort()
    return res


def get_compatible_apps(pattern=None):
    apps = [app for app in COMPATIBLE_APPS if
            pattern is None or app.name.lower().find(pattern.lower()) != -1]

    if pattern:
        for app in apps:  # handle exact match
            if pattern.lower() == app.name.lower():
                return [app]

    return apps


def get_compatible_app_names(pattern=None):
    res = [app.name for app in get_compatible_apps(pattern)]
    res.sort()
    return res


def get_app_path(app_name):
    return join(get_apps_dir(), app_name)


def make_run_script(run_config, run_script):
    idea_script = get_launch_script(run_config.path_to_app)

    with open(idea_script, 'r') as src, open(run_script, 'w') as dst:
        for line in src:
            if line.startswith("IDE_BIN_HOME"):
                line = f'IDE_BIN_HOME={join(run_config.path_to_app, "bin")}\n'
            elif line.find("classpath") != -1:
                line = f'  -classpath "$CLASSPATH:{PROJECTOR_SERVER_DIR}/*" \\\n'
            elif line.find(IDEA_PATH_SELECTOR) != -1:
                if run_config.ide_config_dir:
                    line = f'  -D{IDEA_PATH_SELECTOR}={run_config.ide_config_dir} \\\n'
            elif line.find(IDEA_RUN_CLASS) != -1:
                line = f'  -Dorg.jetbrains.projector.server.port={run_config.projector_port} \\\n'
                line += f'  -Dorg.jetbrains.projector.server.classToLaunch={IDEA_RUN_CLASS} \\\n'
                line += f'  {PROJECTOR_RUN_CLASS}\n'

            dst.write(line)

    st = stat(run_script)
    chmod(run_script, st.st_mode | 0o0111)


@dataclass()
class ProductInfo:
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


@dataclass()
class Version:
    year: int
    quart: int
    last: int


def parse_version(version):
    parsed = version.split(".")
    v = Version(int(parsed[0]), int(parsed[1]), int(parsed[2] if len(parsed) > 2 else -1))

    return v


def get_data_dir_from_script(run_script):
    with open(run_script, 'r') as f:
        for line in f:
            pos = line.find(IDEA_PATH_SELECTOR)

            if pos != -1:
                parts = line.split("=")

                if len(parts) < 2:
                    raise Exception(f"Unable to parse {IDEA_PATH_SELECTOR} line.")

                return parts[1].split(" ")[0]

    raise Exception("Unable to find data directory in the launch script.")


def get_product_info(app_path):
    prod_info_path = join(app_path, PRODUCT_INFO)
    with open(prod_info_path, "r") as f:
        data = json.load(f)

        pi = ProductInfo(data['name'], data['version'], data['buildNumber'],
                         data['productCode'], '', data['svgIconPath'],
                         data['launch'][0]['os'],
                         data['launch'][0]['launcherPath'],
                         data['launch'][0]['javaExecutablePath'],
                         data['launch'][0]['vmOptionsFilePath'],
                         data['launch'][0]['startupWmClass'])

        v = parse_version(pi.version)

        if v.year >= 2020 and v.quart >= 2:
            pi.data_dir = data['dataDirectoryName']
        else:
            pi.data_dir = get_data_dir_from_script(join(app_path, pi.launcher_path))

        return pi


def get_launch_script(app_path):
    prod_info = get_product_info(app_path)
    return join(app_path, prod_info.launcher_path)


def get_bin_dir(app_path):
    run_script = get_launch_script(app_path)
    return dirname(run_script)


CONFIG_PREFIX = expanduser('~/')
VER_2020_CONFIG_PREFIX = expanduser('~/.config/JetBrains')


def get_config_dir(app_path):
    pi = get_product_info(app_path)
    v = parse_version(pi.version)

    if v.year >= 2020:
        return join(VER_2020_CONFIG_PREFIX, pi.data_dir)

    return join(join(CONFIG_PREFIX, '.' + pi.data_dir), 'config')


PLUGIN_2020_PREFIX = expanduser('~/.local/share/JetBrains')


def get_plugin_dir(app_path):
    pi = get_product_info(app_path)
    v = parse_version(pi.version)

    if v.year >= 2020:
        return join(PLUGIN_2020_PREFIX, pi.data_dir)

    return join(get_config_dir(app_path), "plugins")
