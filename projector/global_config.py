import sys
from os import listdir, mkdir
from os.path import dirname, join, expanduser, abspath

USER_HOME = expanduser("~")
INSTALL_DIR = dirname(abspath(__file__))
HTTP_DIR = join(INSTALL_DIR, "bundled", "client")
PROJECTOR_SERVER_DIR = join(INSTALL_DIR, "bundled", "server")
PROJECTOR_MARKDOWN_PLUGIN_DIR = join(INSTALL_DIR, "bundled", "projector-markdown-plugin")


def get_server_file_name():
    file_list = [file_name for file_name in listdir(PROJECTOR_SERVER_DIR)
                 if file_name.startswith('projector-server') and file_name.endswith('.jar')]

    if len(file_list) == 1:
        return join(PROJECTOR_SERVER_DIR, file_list[0])

    raise Exception()


try:
    SERVER_JAR = get_server_file_name()
except Exception as e:
    print("Cannot find a Projector server. Please reinstall Projector.")
    sys.exit(2)

DEF_CONFIG_DIR = '.projector'

config_dir = join(USER_HOME, DEF_CONFIG_DIR)


def get_apps_dir():
    return join(config_dir, "apps")


def get_run_configs_dir():
    return join(config_dir, "configs")


def get_download_cache_dir():
    return join(config_dir, "cache")


def init_config_dir():
    mkdir(config_dir)
    mkdir(get_apps_dir())
    mkdir(get_run_configs_dir())
    mkdir(get_download_cache_dir())
