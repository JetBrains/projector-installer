# Copyright 2000-2020 JetBrains s.r.o.
# Use of this source code is governed by the Apache 2.0 license that can be found
# in the LICENSE file.


"""Run configurations related functions"""

from os import listdir, rename
from os.path import join, isdir
from shutil import rmtree
from typing import Optional, Dict, List, TextIO
from fcntl import lockf, LOCK_EX, LOCK_NB
from dataclasses import dataclass

import configparser

from .apps import get_app_path
from .global_config import get_run_configs_dir

CONFIG_INI_NAME = 'config.ini'
RUN_SCRIPT_NAME = 'run.sh'
LOCK_FILE_NAME: str = 'run.lock'


@dataclass
class RunConfig:
    """Run config dataclass"""

    # pylint: disable=too-many-instance-attributes
    name: str
    path_to_app: str
    projector_port: int
    token: str
    password: str
    ro_password: str
    toolbox: bool
    custom_names: str

    def is_secure(self) -> bool:
        """Checks if secure configuration"""
        return self.token != ''

    def is_password_protected(self) -> bool:
        """Checks if run config is password protected"""
        return self.password != ''


def load_config(config_name: str) -> RunConfig:
    """Loads specified config from disk."""
    config = configparser.ConfigParser()
    config_path = join(get_run_configs_dir(), config_name, CONFIG_INI_NAME)
    config.read(config_path)

    return RunConfig(config_name,
                     config.get('IDE', 'PATH'),
                     config.getint('PROJECTOR', 'PORT'),
                     config.get('SSL', 'TOKEN', fallback=''),
                     config.get('PASSWORDS', 'PASSWORD', fallback=''),
                     config.get('PASSWORDS', 'RO_PASSWORD', fallback=''),
                     config.getboolean('TOOLBOX', 'TOOLBOX', fallback=False),
                     config.get('FQDNS', 'FQDNS', fallback=''))


def get_run_script_path(config_name: str) -> str:
    """Returns full path to projector run script"""
    return join(get_run_configs_dir(), config_name, RUN_SCRIPT_NAME)


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


def get_used_projector_ports() -> List[int]:
    """Returns list of ports, used by projector servers in existing configs."""
    return [rc.projector_port for rc in get_run_configs().values()]


def get_configs_with_app(app_name: str) -> List[str]:
    """Returns list of configs which referees to given app name."""
    app_path = get_app_path(app_name)
    return [k for k, v in get_run_configs().items() if v.path_to_app == app_path]


def get_lock_file_name(config_name: str) -> str:
    """Return full path to lock file for given config name"""
    return join(get_run_configs_dir(), config_name, LOCK_FILE_NAME)


def lock_config(config_name: str) -> Optional[TextIO]:
    """Create lock file for run config"""
    file = open(get_lock_file_name(config_name), 'w')

    try:
        lockf(file, LOCK_EX + LOCK_NB)
    except OSError:
        file.close()
        return None

    return file


def release_config(lock: TextIO) -> None:
    """Release lock file"""
    lock.close()
