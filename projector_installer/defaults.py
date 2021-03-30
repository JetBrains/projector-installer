#  Copyright 2000-2021 JetBrains s.r.o.
#  Use of this source code is governed by the Apache 2.0 license that can be found
#  in the LICENSE file.

"""Projector defaults related stuff"""
import configparser
from dataclasses import dataclass
from os.path import join, isfile
from typing import Optional, ClassVar

from projector_installer.global_config import config_dir

DEFAULTS_INI = 'defaults.ini'


@dataclass
class Defaults:
    """Projector defaults storage"""
    HOST: ClassVar[str] = '0.0.0.0'  # pylint: disable=invalid-name
    host: str = ''

    def get_host(self, host: Optional[str] = '') -> str:
        """Returns default value for hostname"""
        if host:
            return host

        if self.host:
            return self.host

        return Defaults.HOST


def get_path_to_defaults() -> str:
    """Returns full path to defaults"""
    return join(config_dir, DEFAULTS_INI)


def get_defaults() -> Defaults:
    """Read default settings"""
    parser = configparser.ConfigParser(strict=False, interpolation=None)
    defaults_path = get_path_to_defaults()

    if not isfile(defaults_path):
        return Defaults()

    parser.read(defaults_path)

    return Defaults(parser.get('PROJECTOR', 'HOST', fallback=''))


def save_defaults(defaults: Defaults) -> None:
    """Save projector defaults file"""
    parser = configparser.ConfigParser(strict=False, interpolation=None)
    parser['PROJECTOR'] = {}
    parser['PROJECTOR']['HOST'] = defaults.host

    with open(get_path_to_defaults(), 'w') as file:
        parser.write(file)
