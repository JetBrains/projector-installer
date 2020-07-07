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
    path_to_app: str
    ide_config_dir: str
    projector_port: int
    http_address: str
    http_port: int


def load_config(config_name):
    config = configparser.ConfigParser()
    config_path = join(get_run_configs_dir(), config_name, CONFIG_INI_NAME)
    config.read(config_path)

    return RunConfig(config.get("IDE", "PATH"),
                     config.get("IDE", "CONFIG_DIR"),
                     config.getint("PROJECTOR", "PORT"),
                     config.get("HTTP.SERVER", "ADDRESS"),
                     config.getint("HTTP.SERVER", "PORT"))


def get_run_script(config_name):
    return join(get_run_configs_dir(), config_name, RUN_SCRIPT_NAME)


def generate_run_script(config_name):
    run_script = get_run_script(config_name)
    run_config = get_run_configs()[config_name]

    make_run_script(run_config, run_script)


def save_config(config_name, run_config: RunConfig):
    config = configparser.ConfigParser()
    config["IDE"] = {}
    config["IDE"]["PATH"] = run_config.path_to_app
    config["IDE"]["CONFIG_DIR"] = run_config.ide_config_dir

    config["PROJECTOR"] = {}
    config["PROJECTOR"]["PORT"] = str(run_config.projector_port)

    config["HTTP.SERVER"] = {}
    config["HTTP.SERVER"]["ADDRESS"] = run_config.http_address
    config["HTTP.SERVER"]["PORT"] = str(run_config.http_port)

    config_path = join(get_run_configs_dir(), config_name)

    if not path.isdir(config_path):
        mkdir(config_path)

    config_path = join(config_path, CONFIG_INI_NAME)

    with open(config_path, 'w') as configfile:
        config.write(configfile)

    generate_run_script(config_name)


def get_run_configs(pattern=None):
    res = {}

    for config_name in listdir(get_run_configs_dir()):
        if pattern and config_name.lower().find(pattern.lower()) == -1:
            continue

        config = load_config(config_name)
        res[config_name] = config

    return res


def get_run_config_names(pattern=None):
    res = list(get_run_configs(pattern).keys())
    res.sort()
    return res


def delete_config(config_name):
    config_path = join(get_run_configs_dir(), config_name)
    rmtree(config_path, ignore_errors=True)


def rename_config(from_name, to_name):
    from_path = join(get_run_configs_dir(), from_name)
    to_path = join(get_run_configs_dir(), to_name)
    rename(from_path, to_path)


def make_config_name(app_name):
    pos = app_name.find("-")

    if pos != -1:
        return app_name[0:pos]

    return app_name


def is_known_config(config_name):
    return config_name in get_run_configs().keys()


def validate_run_config(run_config):
    if not isdir(run_config.path_to_app):
        raise Exception(f"IDE path does not exist: {run_config.path_to_app}")


def get_used_http_ports():
    return [rc.http_port for rc in get_run_configs().values()]


def get_used_projector_ports():
    return [rc.projector_port for rc in get_run_configs().values()]


def get_configs_with_app(app_name):
    p = get_app_path(app_name)
    return [k for k, v in get_run_configs().items() if v.path_to_app == p]
