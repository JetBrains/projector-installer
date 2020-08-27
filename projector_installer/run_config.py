# Copyright 2000-2020 JetBrains s.r.o.
# Use of this source code is governed by the Apache 2.0 license that can be found
# in the LICENSE file.


"""Run configurations related functions"""

from os import listdir, mkdir, path, rename
from os.path import join, isdir
from shutil import rmtree
from typing import Optional, Dict, List
import configparser

from .apps import get_app_path, make_run_script
from .global_config import get_run_configs_dir, RunConfig
from .ide_configuration import install_own_markdown_plugin

CONFIG_INI_NAME = 'config.ini'
RUN_SCRIPT_NAME = 'run.sh'


def load_config(config_name: str) -> RunConfig:
    """Loads specified config from disk."""
    config = configparser.ConfigParser()
    config_path = join(get_run_configs_dir(), config_name, CONFIG_INI_NAME)
    config.read(config_path)

    return RunConfig(config.get('IDE', 'PATH'),
                     config.get('IDE', 'CONFIG_DIR'),
                     config.getint('PROJECTOR', 'PORT'),
                     config.get('HTTP.SERVER', 'ADDRESS'),
                     config.getint('HTTP.SERVER', 'PORT'))


def get_run_script(config_name: str) -> str:
    """Returns fuill path to projector run script"""
    return join(get_run_configs_dir(), config_name, RUN_SCRIPT_NAME)


def generate_run_script(config_name: str) -> None:
    """Generates projector run script"""
    run_script = get_run_script(config_name)
    run_config = get_run_configs()[config_name]

    make_run_script(run_config, run_script)


def save_config(config_name: str, run_config: RunConfig) -> None:
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


def get_run_configs(pattern: Optional[str] = None) -> Dict[str, RunConfig]:
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


def get_run_config_names(pattern: Optional[str] = None) -> List[str]:
    """Get sorted run config names list, matched to given pattern."""
    res = list(get_run_configs(pattern).keys())
    res.sort()
    return res


def delete_config(config_name: str) -> None:
    """Removes specified config."""
    config_path = join(get_run_configs_dir(), config_name)
    rmtree(config_path, ignore_errors=True)


def rename_config(from_name: str, to_name: str) -> None:
    """Renames config from_name to to_name."""
    from_path = join(get_run_configs_dir(), from_name)
    to_path = join(get_run_configs_dir(), to_name)
    rename(from_path, to_path)


def make_config_name(app_name: str) -> str:
    """Creates config name from application name."""
    pos = app_name.find(' ')

    if pos != -1:
        return app_name[0:pos]

    return app_name


def validate_run_config(run_config: RunConfig) -> None:
    """Checks given config for validity."""
    if not isdir(run_config.path_to_app):
        raise ValueError(f'IDE path does not exist: {run_config.path_to_app}')

    if run_config.http_port == run_config.projector_port:
        raise ValueError('HTTP port can\'t be equal to projector port.')


def get_used_http_ports() -> List[int]:
    """Returns list of ports, used by http servers in existing configs."""
    return [rc.http_port for rc in get_run_configs().values()]


def get_used_projector_ports() -> List[int]:
    """Returns list of ports, used by projector servers in existing configs."""
    return [rc.projector_port for rc in get_run_configs().values()]


def get_used_ports() -> List[int]:
    """Returns list of ports, used either by projector or http servers in existing configs."""
    return get_used_http_ports() + get_used_projector_ports()


def get_configs_with_app(app_name: str) -> List[str]:
    """Returns list of configs which referees to given app name."""
    app_path = get_app_path(app_name)
    return [k for k, v in get_run_configs().items() if v.path_to_app == app_path]


def update_markdown_plugin(run_config: RunConfig) -> None:
    """
    Updates markdown plugin in specified config with bundled version.
    Useful after script update.
    """
    install_own_markdown_plugin(run_config.path_to_app)
