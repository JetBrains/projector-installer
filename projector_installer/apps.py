# Copyright 2000-2020 JetBrains s.r.o.
# Use of this source code is governed by the Apache 2.0 license that can be found
# in the LICENSE file.


"""Application management functions."""
import shutil
import sys
import os
from os import listdir
from os.path import join, dirname, isfile, isdir, basename, expanduser
from distutils.version import LooseVersion
from typing import Optional, List, Tuple
from dataclasses import dataclass
import json
from xml.etree.ElementTree import Element, parse, SubElement

from .global_config import get_apps_dir, get_download_cache_dir
from .utils import unpack_tar_file, expand_path, download_file, \
    create_dir_if_not_exist, is_linux_x86_64

CONFIG_PREFIX = expanduser('~/')
VER_2020_CONFIG_PREFIX = expanduser('~/.config/JetBrains')
ANDROID_STUDIO_CONFIG_PREFIX = expanduser('~/.config/Google')

IDEA_PATH_SELECTOR = 'idea.paths.selector'
IDEA_PROPERTIES_FILE = 'idea.properties'
DISABLED_PLUGINS_FILE = 'disabled_plugins.txt'
FORBID_UPDATE_STRING = 'ide.no.platform.update=Projector'

PLUGIN_2020_PREFIX: str = expanduser('~/.local/share/JetBrains')
ANDROID_STUDIO_PLUGIN_PREFIX = expanduser('~/.local/share/Google')

MPS_LAUNCHER_PATH = 'bin/mps.sh'
MPS_SVG_ICON_PATH = 'bin/mps.svg'
MPS_VM_OPTIONS_PATH = 'bin/mps64.vmoptions'
MPS_STARTUP_WM_CLASS = 'jetbrains-mps'

NOTIFICATIONS_CONFIG = 'notifications.xml'
UPDATES_ATTRIBUTES = {'groupId': 'Plugins updates', 'displayType': 'NONE', 'shouldLog': 'false'}

APP_NAME_FILE_EXTENSION = 'app_name'

TOOLBOX_DEFAULT_DIR = '~/.local/share/JetBrains/Toolbox/'
TOOLBOX_SETTINGS = '.settings.json'
CHANNEL_SETTINGS_FILE = '.channel.settings.json'


def get_installed_apps(pattern: Optional[str] = None) -> List[str]:
    """Returns sorted list of installed apps, matched given pattern."""
    apps_dir = get_apps_dir()

    if not isdir(apps_dir):
        return []

    res = [file_name for file_name in listdir(apps_dir) if
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
    version_suffix: str
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


class VersionFormatError(Exception):
    """VersionFormatError"""


def parse_version(version: str) -> Version:
    """Parses version string to Version class."""
    parsed = version.split(".")

    try:
        return Version(int(parsed[0]), int(parsed[1]), int(parsed[2] if len(parsed) > 2 else -1))
    except ValueError:
        return Version(0, 0, -1)
    except IndexError as index_error:
        raise VersionFormatError from index_error


def get_data_dir_from_script(run_script: str) -> str:
    """Returns idea data dir from run script."""
    with open(run_script, mode='r', encoding='utf-8') as file:
        for line in file:
            pos = line.find(IDEA_PATH_SELECTOR)

            if pos != -1:
                parts = line.split('=')

                if len(parts) < 2:
                    raise Exception(f'Unable to parse {IDEA_PATH_SELECTOR} line.')

                return parts[1].split(' ')[0]

    raise Exception('Unable to find data directory in the launch script.')


class UnknownIDEException(Exception):
    """Unknown IDE exception"""


def is_mps_dir(app_path: str) -> bool:
    """Check if given path is MPS app directory"""
    return isfile(join(app_path, MPS_LAUNCHER_PATH))


def get_mps_version(app_path: str) -> Tuple[str, str]:
    """Extract MPS version and build number from build.number file"""
    pairs = map(lambda x: x.split('='),
                [line.strip() for line in open(join(app_path, 'build.number'),
                                               mode='r', encoding='utf-8')])
    data = {elem[0]: elem[1] for elem in pairs}
    return data['version'], data['build.number']


def get_mps_product_info(app_path: str) -> ProductInfo:
    """Construct MPS ProductInfo"""

    if not is_mps_dir(app_path):
        raise UnknownIDEException(app_path)

    version, build_number = get_mps_version(app_path)

    return ProductInfo(name='MPS', version=version, version_suffix='', build_number=build_number,
                       product_code='MPS', data_dir='', svg_icon_path=MPS_SVG_ICON_PATH,
                       os='linux', launcher_path=MPS_LAUNCHER_PATH, java_exec_path='jbr/bin/java',
                       vm_options_path=MPS_VM_OPTIONS_PATH, startup_wm_class=MPS_STARTUP_WM_CLASS)


def get_product_info(app_path: str) -> ProductInfo:
    """Parses product info file to ProductInfo class."""
    prod_info_path = join(app_path, PRODUCT_INFO)

    try:
        with open(prod_info_path, mode='r', encoding='utf-8') as file:
            data = json.load(file)
            java_exec_path = 'jre/bin/java'
            version_suffix = ''

            if 'versionSuffix' in data:
                version_suffix = data['versionSuffix']

            if 'javaExecutablePath' in data['launch'][0]:
                java_exec_path = data['launch'][0]['javaExecutablePath']

            product_info = ProductInfo(name=data['name'],
                                       version=data['version'],
                                       version_suffix=version_suffix,
                                       build_number=data['buildNumber'],
                                       product_code=data['productCode'],
                                       data_dir='',
                                       svg_icon_path=data['svgIconPath'],
                                       os=data['launch'][0]['os'],
                                       launcher_path=data['launch'][0]['launcherPath'],
                                       java_exec_path=java_exec_path,
                                       vm_options_path=data['launch'][0]['vmOptionsFilePath'],
                                       startup_wm_class=data['launch'][0]['startupWmClass'])

            version = parse_version(product_info.version)

            if version.year >= 2020 and version.quart >= 2:
                product_info.data_dir = data['dataDirectoryName']
            else:
                product_info.data_dir = get_data_dir_from_script(
                    join(app_path, product_info.launcher_path))
    except FileNotFoundError:  # MPS does not have product_info
        product_info = get_mps_product_info(app_path)

    return product_info


def get_launch_script(app_path: str) -> str:
    """Returns full path to launch script by ide path."""
    prod_info = get_product_info(app_path)
    return join(app_path, prod_info.launcher_path)


def get_bin_dir(app_path: str) -> str:
    """Get full path to ide bin dir."""
    run_script = get_launch_script(app_path)
    return dirname(run_script)


def is_android_studio(product_info: ProductInfo) -> bool:
    """Returns True if given product info corresponds AS"""
    return product_info.product_code == 'AI'


def is_mps(product_info: ProductInfo) -> bool:
    """Returns True if given product info corresponds MPS"""
    return product_info.product_code == 'MPS'


def get_java_path(app_path: str) -> str:
    """Returns full path to bundled or system java."""
    if not is_linux_x86_64():
        java_path = shutil.which('java')

        if not java_path:
            print('No java found in system, please install openjdk 11. Exiting ...')
            sys.exit(1)

        return java_path

    product_info = get_product_info(app_path)
    return join(app_path, product_info.java_exec_path)


def get_app_name_cache_file(file_path: str) -> str:
    """Returns path to app name cache file"""
    return f'{file_path}.{APP_NAME_FILE_EXTENSION}'


def is_installed(file_path: str) -> bool:
    """Checks if file with app_name is already exist"""
    cache_file_path = get_app_name_cache_file(file_path)
    return isfile(cache_file_path)


def get_app_name_for(file_path: str) -> str:
    """Returns app_name from saved file"""
    with open(get_app_name_cache_file(file_path), mode='r', encoding='utf-8') as file:
        return file.read()


def save_app_name_for(file_path: str, app_name: str) -> None:
    """Saves app name in cache file"""
    with open(get_app_name_cache_file(file_path), mode='w', encoding='utf-8') as file:
        file.write(app_name)


def is_matched_app_name_file(file_path: str, app_name: str) -> bool:
    """Returns True if given file is app name file, corresponding to the given app_name"""
    if file_path.endswith(APP_NAME_FILE_EXTENSION):
        with open(file_path, mode='r', encoding='utf-8') as file:
            return file.read() == app_name

    return False


def get_app_name_files_for_app(app_name: str) -> List[str]:
    """Returns list of app name files with given app_name"""
    cache_dir = get_download_cache_dir()
    return [join(cache_dir, file) for file in listdir(cache_dir) if
            is_matched_app_name_file(join(cache_dir, file), app_name)]


def remove_app_name_files(app_name: str) -> None:
    """Removes all app name files with given app_name"""
    for file_path in get_app_name_files_for_app(app_name):
        os.remove(file_path)


# There are a number of complications with directory name in application archive file:
# 1. We can't guess dir name from archive file name - different products uses different conventions
# 2. Some applications (MPS, Android Studio etc.) have the same directory name for different
# application versions. To deal with this we have to return app_name from unpack procedure.
def unpack_app(file_path: str) -> str:
    """Unpacks specified file to app directory."""
    if is_installed(file_path):  # Check if we already unpack the app
        return get_app_name_for(file_path)

    app_name = unpack_tar_file(file_path, get_apps_dir())

    # For android studio - ensure that app directory has unique name
    app_path = get_app_path(app_name)
    product_info = get_product_info(app_path)

    if is_android_studio(product_info):
        versioned_name = app_name + "_" + product_info.version.replace(' ', '_')
        new_path = get_app_path(versioned_name)
        shutil.rmtree(new_path, ignore_errors=True)
        os.rename(app_path, new_path)
        app_name = versioned_name
    elif is_mps(product_info):
        new_path = get_app_path(product_info.build_number)
        shutil.rmtree(new_path, ignore_errors=True)
        os.rename(app_path, new_path)
        app_name = product_info.build_number

    save_app_name_for(file_path, app_name)

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
    return isfile(prod_info_path) or is_mps_dir(app_path)


def get_toolbox_dir() -> str:
    """Returns full path to toolbox dir"""
    return expand_path(TOOLBOX_DEFAULT_DIR)


def get_toolbox_settings_file() -> str:
    """Returns path to toolbox config"""
    return join(get_toolbox_dir(), TOOLBOX_SETTINGS)


def is_toolbox_installed() -> bool:
    """Checks if toolbox is installed for current user"""
    ret: bool = isdir(get_toolbox_dir())
    ret = ret and isfile(get_toolbox_settings_file())
    return ret


def get_toolbox_install_location() -> str:
    """
    Returns path to toolbox install location or empty string if toolbox is not installed
    """

    if not is_toolbox_installed():
        return ''

    with open(get_toolbox_settings_file(), mode='r', encoding='utf-8') as settings_file:
        data = json.load(settings_file)

        if 'install_location' in data:
            return str(data['install_location'])

        return get_toolbox_dir()


def is_toolbox_path(app_path: str) -> bool:
    """Checks if given path is toolbox channel path"""
    return get_path_to_toolbox_channel(app_path) is not None


def get_toolbox_apps_location() -> str:
    """Returns path to toolbox directory with installed apps"""
    location = get_toolbox_install_location()

    if location:
        return join(location, 'apps')

    return ''


def get_path_to_toolbox_channel(path: str) -> Optional[str]:
    """"Returns path to toolbox channel"""
    apps_path = get_toolbox_apps_location()
    path = expand_path(path)
    pos = path.find(apps_path)

    if pos >= 0:
        ch_path = path.rstrip('/')
        ch_pos = ch_path.find('ch-')

        if ch_pos > pos:
            sep_pos = ch_path.find('/', ch_pos + 1)

            if sep_pos < 0:
                return ch_path

            return ch_path[:sep_pos]

    return None


FORBIDDEN_TOOLBOX_APP_LIST = ['JetBrainsGateway', 'Projector', 'Toolbox']


def get_toolbox_managed_app_path_list() -> List[str]:
    """Returns list of toolbox-managed apps paths"""
    apps_dir = get_toolbox_apps_location()
    pre = [appname for appname in os.listdir(apps_dir) if isdir(join(apps_dir, appname))
           and appname not in FORBIDDEN_TOOLBOX_APP_LIST]

    pre.sort()
    res = []

    for app_name in pre:
        app_dir = join(apps_dir, app_name)

        for channel in os.listdir(app_dir):
            full_path = join(app_dir, channel)
            if channel.startswith('ch-') and isdir(full_path):
                if get_path_to_latest_app(full_path) is not None:
                    res.append(full_path)

    return res


def get_toolbox_custom_name(app_path: str) -> str:
    """Returns the custom name for toolbox-managed app"""
    file_path = join(app_path, CHANNEL_SETTINGS_FILE)

    if isfile(file_path):
        with open(file_path, mode='r', encoding='utf-8') as file:
            data = json.load(file)

            if 'custom_name' in data:
                return str(data['custom_name'])

    return ''


def get_toolbox_app_channel(app_path: str) -> str:
    """Get toolbox app channel by path"""
    pos = app_path.find('ch-')

    if pos > 0:
        return app_path[pos:]

    return ''


def get_toolbox_app_name(app_path: str) -> str:
    """Returns toolbox app name"""
    name = get_toolbox_custom_name(app_path)

    if not name:
        prefix_len = len(get_toolbox_apps_location())
        name = app_path[prefix_len + 1:]
        pos = name.find('ch-')
        name = name[:pos - 1]

    return name


def toolbox_path_to_display_name(app_path: str) -> str:
    """Maps toolbox path to display name """
    toolbox_name = get_toolbox_app_name(app_path)
    latest = get_path_to_latest_app(app_path)
    prod_info = None

    if latest is not None:
        prod_info = get_product_info(latest)

    channel = get_toolbox_app_channel(app_path)

    if prod_info:
        return f'{prod_info.name}/{channel} ({toolbox_name}, {prod_info.version})'

    return f'{toolbox_name}/{channel}'


def get_toolbox_managed_apps() -> List[str]:
    """Returns list of toolbox managed apps"""
    path_list = get_toolbox_managed_app_path_list()
    res = list(map(toolbox_path_to_display_name, path_list))
    res.sort()

    return res


def get_path_to_toolbox_app(toolbox_app_name: str) -> Optional[str]:
    """Returns path to toolbox app/channel by toolbox paa name """
    return next(
        filter(lambda s: toolbox_path_to_display_name(s) == toolbox_app_name,
               get_toolbox_managed_app_path_list()))


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

    with open(file_name, mode='r', encoding='utf-8') as file:
        lines = [line.strip() for line in file]
        return plugin_name in lines


def disable_plugin(file_name: str, plugin_name: str) -> None:
    """Disables specified plugin"""
    directory = dirname(file_name)
    create_dir_if_not_exist(directory)

    with open(file_name, mode='a', encoding='utf-8') as file:
        file.write(f'{plugin_name}')


def get_ide_properties_file(app_path: str) -> str:
    """Returns path to ide properties file"""
    bin_dir = get_bin_dir(app_path)
    return join(bin_dir, IDEA_PROPERTIES_FILE)


def is_updates_forbidden(app_path: str) -> bool:
    """Returns True if updates for specified IDE is already forbidden"""
    prop_file = get_ide_properties_file(app_path)
    with open(prop_file, mode='r', encoding='utf-8') as file:
        lines = file.read().splitlines()
        return FORBID_UPDATE_STRING in lines


def forbid_updates_for(app_path: str) -> None:
    """Forbids IDEA platform update for specified app."""

    if not is_updates_forbidden(app_path):
        prop_file = get_ide_properties_file(app_path)

        with open(prop_file, mode='a', encoding='utf-8') as file:
            file.write(FORBID_UPDATE_STRING)


def download_and_install(url: str) -> str:
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
    forbid_updates_for(res)

    return res


def get_config_dir(app_path: str) -> str:
    """Returns ide config directory."""
    product_info = get_product_info(app_path)
    version = parse_version(product_info.version)

    if is_android_studio(product_info):
        return join(ANDROID_STUDIO_CONFIG_PREFIX, product_info.data_dir)

    if version.year >= 2020:
        return join(VER_2020_CONFIG_PREFIX, product_info.data_dir)

    return join(join(CONFIG_PREFIX, '.' + product_info.data_dir), 'config')


def get_plugins_dir(app_path: str) -> str:
    """Returns full path to application plugin directory."""
    product_info = get_product_info(app_path)
    version = parse_version(product_info.version)

    if is_android_studio(product_info):
        return join(ANDROID_STUDIO_PLUGIN_PREFIX, product_info.data_dir)

    if version.year >= 2020:
        return join(PLUGIN_2020_PREFIX, product_info.data_dir)

    return join(get_config_dir(app_path), "plugins")


NO_PLUGIN_NOTIFICATION = """
<application>
  <component name="NotificationConfiguration">
    <notification groupId="Plugins updates" displayType="NONE" shouldLog="false" />
  </component>
</application>
"""


def forbid_plugin_update_notifications_in_file(notifications_config: str) -> None:
    """Forbids plugin update notifications in given file"""
    parsed = parse(notifications_config)
    tree: Element = parsed.getroot()

    try:
        nodes = tree.findall('./component/notification[@groupId="Plugins updates"]')

        if len(nodes) < 1:
            raise KeyError

        node = nodes[0]

        if node.attrib is None:
            node.attrib = UPDATES_ATTRIBUTES
        else:
            node.attrib = {**node.attrib, **UPDATES_ATTRIBUTES}

    except KeyError:
        try:
            nodes = tree.findall('./component')

            if len(nodes) > 0:
                node = nodes[0]
                SubElement(node, 'notification', UPDATES_ATTRIBUTES)

        except KeyError:
            pass

    parsed.write(notifications_config, encoding='utf-8')


def forbid_plugin_update_notifications(options_dir: str) -> None:
    """Forbids notification on plugin updates"""
    notifications_config = join(options_dir, NOTIFICATIONS_CONFIG)
    if not isfile(notifications_config):
        os.makedirs(options_dir, exist_ok=True)

        with (open(notifications_config, mode='w', encoding='utf-8')) as file:
            file.write(NO_PLUGIN_NOTIFICATION)
    else:
        forbid_plugin_update_notifications_in_file(notifications_config)
