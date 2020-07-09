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

"""Run configurations related functions"""

from os import listdir, mkdir, path, rename
from os.path import join, isdir
from shutil import rmtree
from dataclasses import dataclass
import configparser

from .apps import get_app_path, make_run_script
from .global_config import get_run_configs_dir

CONFIG_INI_NAME = 'config.ini'
RUN_SCRIPT_NAME = 'run.sh'


@dataclass
class RunConfig:
    """Run config dataclass"""
    path_to_app: str
    ide_config_dir: str
    projector_port: int
    http_address: str
    http_port: int


def load_config(config_name):
    """Loads specified config from disk."""
    config = configparser.ConfigParser()
    config_path = join(get_run_configs_dir(), config_name, CONFIG_INI_NAME)
    config.read(config_path)

    return RunConfig(config.get('IDE', 'PATH'),
                     config.get('IDE', 'CONFIG_DIR'),
                     config.getint('PROJECTOR', 'PORT'),
                     config.get('HTTP.SERVER', 'ADDRESS'),
                     config.getint('HTTP.SERVER', 'PORT'))


def get_run_script(config_name):
    """Returns fuill path to projector run script"""
    return join(get_run_configs_dir(), config_name, RUN_SCRIPT_NAME)


def generate_run_script(config_name: str):
    """Generates projector run script"""
    run_script = get_run_script(config_name)
    run_config = get_run_configs()[config_name]

    make_run_script(run_config, run_script)


def save_config(config_name: str, run_config: RunConfig):
    """Saves given run config."""
    config = configparser.ConfigParser()
    config['IDE'] = {}
    config['IDE']['PATH'] = run_config.path_to_app
    config['IDE']['CONFIG_DIR'] = run_config.ide_config_dir

    config['PROJECTOR'] = {}
    config['PROJECTOR']['PORT'] = str(run_config.projector_port)

    config['HTTP.SERVER'] = {}
    config['HTTP.SERVER']['ADDRESS'] = run_config.http_address
    config['HTTP.SERVER']['PORT'] = str(run_config.http_port)

    config_path = join(get_run_configs_dir(), config_name)

    if not path.isdir(config_path):
        mkdir(config_path)

    config_path = join(config_path, CONFIG_INI_NAME)

    with open(config_path, 'w') as configfile:
        config.write(configfile)

    generate_run_script(config_name)


def get_run_configs(pattern=None):
    """Get run configs, matched given pattern."""
    res = {}

    for config_name in listdir(get_run_configs_dir()):
        if pattern and config_name.lower().find(pattern.lower()) == -1:
            continue

        config = load_config(config_name)

        if pattern == config_name:
            return {config_name: config}

        res[config_name] = config

    return res


def get_run_config_names(pattern=None):
    """Get sorted run config names list, matched to given pattern."""
    res = list(get_run_configs(pattern).keys())
    res.sort()
    return res


def delete_config(config_name):
    """Removes specified config."""
    config_path = join(get_run_configs_dir(), config_name)
    rmtree(config_path, ignore_errors=True)


def rename_config(from_name, to_name):
    """Renames config from_name to to_name."""
    from_path = join(get_run_configs_dir(), from_name)
    to_path = join(get_run_configs_dir(), to_name)
    rename(from_path, to_path)


def make_config_name(app_name):
    """Creates config name from application name."""
    pos = app_name.find('-')

    if pos != -1:
        return app_name[0:pos]

    return app_name


def validate_run_config(run_config):
    """Checks given config for validity."""
    if not isdir(run_config.path_to_app):
        raise IsADirectoryError(f'IDE path does not exist: {run_config.path_to_app}')


def get_used_http_ports():
    """Returns list of ports, used by http servers in existing configs."""
    return [rc.http_port for rc in get_run_configs().values()]


def get_used_projector_ports():
    """Returns list of ports, used by projector servers in existing configs."""
    return [rc.projector_port for rc in get_run_configs().values()]


def get_configs_with_app(app_name: str):
    """Returns list of configs which referees to given app name."""
    app_path = get_app_path(app_name)
    return [k for k, v in get_run_configs().items() if v.path_to_app == app_path]
