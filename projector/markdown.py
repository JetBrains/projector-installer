from .global_config import PROJECTOR_MARKDOWN_PLUGIN_DIR
from .apps import get_config_dir, get_plugin_dir
from os.path import join, isfile, isdir, basename, dirname
from distutils.dir_util import copy_tree
from pathlib import Path

DISABLED_PLUGINS_FILE = 'disabled_plugins.txt'
MARKDOWN_PLUGIN_NAME = 'org.intellij.plugins.markdown'


def is_disabled(file_name, plugin_name):
    if not isfile(file_name):
        return False

    with open(file_name, 'r') as f:
        lines = [line.strip() for line in f]
        return plugin_name in lines


def disable_plugin(file_name, plugin_name):
    dir = dirname(file_name)

    if not isdir(dir):
        p = Path(dir)
        p.mkdir(parents=True, exist_ok=True)

    with open(file_name, 'a') as f:
        f.write(f'{plugin_name}')


def disable_markdown_plugin(app_path):
    config_dir = get_config_dir(app_path)
    file_name = join(config_dir, DISABLED_PLUGINS_FILE)

    if not is_disabled(file_name, MARKDOWN_PLUGIN_NAME):
        disable_plugin(file_name, MARKDOWN_PLUGIN_NAME)


def install_own_markdown_plugin(app_path):
    dest_dir = get_plugin_dir(app_path)
    dest_dir = join(dest_dir, basename(PROJECTOR_MARKDOWN_PLUGIN_DIR))

    copy_tree(PROJECTOR_MARKDOWN_PLUGIN_DIR, dest_dir)


def install_projector_markdown(app_path):
    disable_markdown_plugin(app_path)
    install_own_markdown_plugin(app_path)
