# Copyright 2000-2020 JetBrains s.r.o.
# Use of this source code is governed by the Apache 2.0 license that can be found
# in the LICENSE file.


"""
Ide configuration routines.
"""

from os.path import join, isfile, basename, dirname
from distutils.dir_util import copy_tree
from .global_config import get_projector_markdown_plugin_dir
from .apps import get_config_dir, get_plugin_dir, get_bin_dir
from .utils import create_dir_if_not_exist


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
MARKDOWN_PLUGIN_NAME = 'org.intellij.plugins.markdown'


def disable_markdown_plugin(app_path: str) -> None:
    """Disables markdown plugin"""
    config_dir = get_config_dir(app_path)
    file_name = join(config_dir, DISABLED_PLUGINS_FILE)

    if not is_disabled(file_name, MARKDOWN_PLUGIN_NAME):
        disable_plugin(file_name, MARKDOWN_PLUGIN_NAME)


def install_own_markdown_plugin(app_path: str) -> None:
    """Install projector markdown plugin"""
    destination_dir = get_plugin_dir(app_path)
    destination_dir = join(destination_dir, basename(get_projector_markdown_plugin_dir()))

    copy_tree(get_projector_markdown_plugin_dir(), destination_dir)


def install_projector_markdown_for(app_path: str) -> None:
    """Install projector markdown plugin for specified application."""
    disable_markdown_plugin(app_path)
    install_own_markdown_plugin(app_path)


IDEA_PROPERTIES_FILE = 'idea.properties'
FORBID_UPDATE_STRING = 'ide.no.platform.update=Projector'


def forbid_updates_for(app_path: str) -> None:
    """Forbids IDEA platform update for specified app."""
    bin_dir = get_bin_dir(app_path)
    prop_file = join(bin_dir, IDEA_PROPERTIES_FILE)

    with open(prop_file, 'a') as file:
        file.write(f'{FORBID_UPDATE_STRING}')
