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
Ide configuration routines.
"""

from os.path import join, isfile, basename, dirname
from distutils.dir_util import copy_tree
from .global_config import PROJECTOR_MARKDOWN_PLUGIN_DIR
from .apps import get_config_dir, get_plugin_dir, get_bin_dir
from .utils import create_dir_if_not_exist


def is_disabled(file_name, plugin_name):
    """Checks if given plugin is already disabled"""
    if not isfile(file_name):
        return False

    with open(file_name, 'r') as file:
        lines = [line.strip() for line in file]
        return plugin_name in lines


def disable_plugin(file_name, plugin_name):
    """Disables specified plugin"""
    directory = dirname(file_name)
    create_dir_if_not_exist(directory)

    with open(file_name, 'a') as file:
        file.write(f'{plugin_name}')


DISABLED_PLUGINS_FILE = 'disabled_plugins.txt'
MARKDOWN_PLUGIN_NAME = 'org.intellij.plugins.markdown'


def disable_markdown_plugin(app_path):
    """Disables markdown plugin"""
    config_dir = get_config_dir(app_path)
    file_name = join(config_dir, DISABLED_PLUGINS_FILE)

    if not is_disabled(file_name, MARKDOWN_PLUGIN_NAME):
        disable_plugin(file_name, MARKDOWN_PLUGIN_NAME)


def install_own_markdown_plugin(app_path):
    """Install projector markdown plugin"""
    destination_dir = get_plugin_dir(app_path)
    destination_dir = join(destination_dir, basename(PROJECTOR_MARKDOWN_PLUGIN_DIR))

    copy_tree(PROJECTOR_MARKDOWN_PLUGIN_DIR, destination_dir)


def install_projector_markdown_for(app_path):
    """Install projector markdown plugin for specified application."""
    disable_markdown_plugin(app_path)
    install_own_markdown_plugin(app_path)


IDEA_PROPERTIES_FILE = 'idea.properties'
FORBID_UPDATE_STRING = 'ide.no.platform.update=Projector'


def forbid_updates_for(app_path):
    """Forbids IDEA platform update for specified app."""
    bin_dir = get_bin_dir(app_path)
    prop_file = join(bin_dir, IDEA_PROPERTIES_FILE)

    with open(prop_file, 'a') as file:
        file.write(f'{FORBID_UPDATE_STRING}')
