# Copyright 2000-2020 JetBrains s.r.o.
# Use of this source code is governed by the Apache 2.0 license that can be found
# in the LICENSE file.


"""
Ide configuration routines.
"""

from os.path import join, isfile, dirname
from .apps import get_bin_dir
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
IDEA_PROPERTIES_FILE = 'idea.properties'
FORBID_UPDATE_STRING = 'ide.no.platform.update=Projector'


def forbid_updates_for(app_path: str) -> None:
    """Forbids IDEA platform update for specified app."""
    bin_dir = get_bin_dir(app_path)
    prop_file = join(bin_dir, IDEA_PROPERTIES_FILE)

    with open(prop_file, 'a') as file:
        file.write(f'{FORBID_UPDATE_STRING}')
