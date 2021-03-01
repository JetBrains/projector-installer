# Copyright 2000-2020 JetBrains s.r.o.
# Use of this source code is governed by the Apache 2.0 license that can be found
# in the LICENSE file.


"""Run configurations related functions"""
import shutil
from os import listdir, rename
from os.path import join, isdir, basename
from shutil import rmtree
from typing import Optional, Dict, List, TextIO, ClassVar
from fcntl import lockf, LOCK_EX, LOCK_NB
from dataclasses import dataclass

import configparser

from .apps import get_app_path, get_path_to_toolbox_channel, \
    get_app_name_from_toolbox_path, get_channel_from_toolbox_path, get_product_name
from .global_config import get_run_configs_dir
from .utils import create_dir_if_not_exist, generate_token

CONFIG_INI_NAME = 'config.ini'
RUN_SCRIPT_NAME = 'run.sh'
LOCK_FILE_NAME: str = 'run.lock'


def get_path_to_config(config_name: str) -> str:
    """Returns path to config dir"""
    return join(get_run_configs_dir(), config_name)


def get_path_to_certificate_dir(config_name: str) -> str:
    """Returns full path to directory with own certificate"""
    return join(get_path_to_config(config_name), 'cert')


@dataclass
class RunConfig:
    # pylint: disable=too-many-instance-attributes
    """Run config dataclass"""
    TESTED: ClassVar[str] = 'tested'  # pylint: disable=invalid-name
    NOT_TESTED: ClassVar[str] = 'not_tested'  # pylint: disable=invalid-name
    UNKNOWN: ClassVar[str] = 'unknown'  # pylint: disable=invalid-name
    HOST_ALL: ClassVar[str] = '*'  # pylint: disable=invalid-name

    name: str
    path_to_app: str
    projector_port: int
    token: str
    password: str
    ro_password: str
    toolbox: bool
    custom_names: str
    certificate: str = ''
    certificate_key: str = ''
    certificate_chain: str = ''
    update_channel: str = UNKNOWN
    projector_host: str = HOST_ALL

    def is_secure(self) -> bool:
        """Checks if secure configuration"""
        return self.token != ''

    def is_password_protected(self) -> bool:
        """Checks if run config is password protected"""
        return self.password != ''

    def get_path(self) -> str:
        """Returns path to config dir"""
        return get_path_to_config(self.name)

    def get_path_to_certificate_dir(self) -> str:
        """Returns full path to directory with own certificate"""
        return get_path_to_certificate_dir(self.name)

    def get_path_to_certificate_file(self) -> str:
        """Returns full path to certificate file"""
        return join(get_path_to_certificate_dir(self.name), self.certificate)

    def get_path_to_key_file(self) -> str:
        """Returns full path to key file"""
        return join(get_path_to_certificate_dir(self.name), self.certificate_key)

    def get_path_to_chain_file(self) -> str:
        """Returns full path to certificate chain file"""
        return join(get_path_to_certificate_dir(self.name), self.certificate_chain)

    def _copy_cert_file(self, path_to_file: str) -> str:
        """Copy file to cert directory"""
        cert_directory = get_path_to_certificate_dir(self.name)
        create_dir_if_not_exist(cert_directory)
        file_name = basename(path_to_file)
        destination = join(get_path_to_certificate_dir(self.name), file_name)
        shutil.copy(path_to_file, destination)

        return file_name

    def make_secure(self) -> None:
        """Generate token (make config secure)"""
        self.token = generate_token()

    def add_certificate(self, path_to_certificate: str,
                        path_to_key: str, path_to_chain: Optional[str]) -> None:
        """Copies certificate file and key file to run config directory"""
        self.certificate = self._copy_cert_file(path_to_certificate)
        self.certificate_key = self._copy_cert_file(path_to_key)
        self.certificate_chain = self._copy_cert_file(path_to_chain) if path_to_chain else ''
        self.make_secure()


def load_config(config_name: str) -> RunConfig:
    """Loads specified config from disk."""
    config = configparser.ConfigParser()
    config_path = join(get_path_to_config(config_name), CONFIG_INI_NAME)
    config.read(config_path)

    return RunConfig(config_name,
                     config.get('IDE', 'PATH'),
                     config.getint('PROJECTOR', 'PORT'),
                     config.get('SSL', 'TOKEN', fallback=''),
                     config.get('PASSWORDS', 'PASSWORD', fallback=''),
                     config.get('PASSWORDS', 'RO_PASSWORD', fallback=''),
                     config.getboolean('TOOLBOX', 'TOOLBOX', fallback=False),
                     config.get('FQDNS', 'FQDNS', fallback=''),
                     config.get('SSL', 'CERTIFICATE_FILE', fallback=''),
                     config.get('SSL', 'KEY_FILE', fallback=''),
                     config.get('SSL', 'CHAIN_FILE', fallback=''),
                     config.get('UPDATE', 'CHANNEL', fallback=RunConfig.UNKNOWN),
                     config.get('PROJECTOR', 'HOST', fallback=RunConfig.HOST_ALL))


def get_run_script_path(config_name: str) -> str:
    """Returns full path to projector run script"""
    return join(get_path_to_config(config_name), RUN_SCRIPT_NAME)


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
    rmtree(get_path_to_config(config_name), ignore_errors=True)


def rename_config(from_name: str, to_name: str) -> None:
    """Renames config from_name to to_name."""
    from_path = get_path_to_config(from_name)
    to_path = get_path_to_config(to_name)
    rename(from_path, to_path)


def make_config_name(app_name: str) -> str:
    """Creates config name from application name."""
    pos = app_name.find(' ')

    if pos != -1:
        return app_name[0:pos]

    return app_name


def get_config_name_from_toolbox_path(toolbox_path: str) -> str:
    """Creates config name from toolbox path"""
    name = get_app_name_from_toolbox_path(toolbox_path)
    channel = get_channel_from_toolbox_path(toolbox_path)

    return f'{name}_Toolbox_{channel}'


def make_config_name_from_path(app_path: str) -> str:
    """Creates config name from application path."""

    toolbox_path = get_path_to_toolbox_channel(app_path)

    if toolbox_path:
        return get_config_name_from_toolbox_path(toolbox_path)

    return get_product_name(app_path)


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
    return join(get_path_to_config(config_name), LOCK_FILE_NAME)


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
