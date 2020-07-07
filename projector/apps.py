from dataclasses import dataclass
import requests
import click
from os.path import join, isfile, getsize, basename, expanduser
from os import listdir, chmod, stat
import tarfile
import json
from .global_config import get_download_cache_dir, get_apps_dir, PROJECTOR_SERVER_DIR

IDEA_RUN_CLASS = 'com.intellij.idea.Main'
PROJECTOR_RUN_CLASS = 'org.jetbrains.projector.server.ProjectorLauncher'
IDEA_PLATFORM_PREFIX = 'idea.platform.prefix'
IDEA_PATH_SELECTOR = 'idea.paths.selector'


@dataclass(frozen=True)
class KnownApp:
    name: str
    url: str


COMPATIBLE_APPS = [
    KnownApp('IntelliJ IDEA Community 2019.3.4', 'https://download.jetbrains.com/idea/ideaIC-2019.3.4.tar.gz'),
    KnownApp('IntelliJ IDEA Community 2020.1.1', 'https://download.jetbrains.com/idea/ideaIC-2020.1.1.tar.gz'),
    KnownApp('IntelliJ IDEA Ultimate 2019.3', 'https://download.jetbrains.com/idea/ideaIU-2019.3.4.tar.gz'),
    KnownApp('IntelliJ IDEA Community 2020.2 EAP', 'https://download.jetbrains.com/idea/ideaIC-202.5103.13.tar.gz'),
    KnownApp('CLion 2019.3.5', 'https://download.jetbrains.com/cpp/CLion-2019.3.5.tar.gz'),
    KnownApp('GoLand 2019.3.4', 'https://download.jetbrains.com/go/goland-2019.3.4.tar.gz'),
    KnownApp('DataGrip 2019.3', 'https://download.jetbrains.com/datagrip/datagrip-2019.3.4.tar.gz'),
    KnownApp('PhpStorm 2019.3', 'https://download.jetbrains.com/webide/PhpStorm-2019.3.4.tar.gz'),
    KnownApp('PyCharm Community 2019.3.4', 'https://download.jetbrains.com/python/pycharm-community-2019.3.4.tar.gz'),
    KnownApp('PyCharm Professional 2019.3.4',
             'https://download.jetbrains.com/python/pycharm-professional-2019.3.4.tar.gz'),
]


def get_installed_apps(pattern=None):
    res = [file_name for file_name in listdir(get_apps_dir()) if
           pattern is None or file_name.lower().find(pattern.lower()) != -1]
    res.sort()
    return res


def get_compatible_apps(pattern=None):
    apps = [app for app in COMPATIBLE_APPS if pattern is None or app.name.lower().find(pattern.lower()) != -1]

    if pattern:
        for app in apps:  # handle exact match
            if pattern.lower() == app.name.lower():
                return [app]

    return apps


def get_compatible_app_names(pattern=None):
    res = [app.name for app in get_compatible_apps(pattern)]
    res.sort()
    return res


CHUNK_SIZE = 4 * 1024 * 1024


def download_app(url):
    parts = url.split("/")
    file_name = parts[-1]
    file_path = join(get_download_cache_dir(), file_name)

    with requests.get(url, stream=True) as req:
        req.raise_for_status()
        total = int(req.headers['Content-Length'])

        if not isfile(file_path) or getsize(file_path) != total:
            with open(file_path, 'wb') as f, click.progressbar(length=total, label=f'Downloading {file_name}') as bar:
                for chunk in req.iter_content(CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
                        bar.update(len(chunk))

    return file_path


def unpack_app(file_path):
    print(f"Unpacking {basename(file_path)}", flush=True)
    tf = tarfile.open(file_path)
    members = tf.getmembers()
    app_name = members[0].name.split('/')[0]

    if app_name in get_installed_apps():
        return app_name

    with click.progressbar(length=len(members), label="Extracting") as bar:
        for i, m in enumerate(members):
            tf.extract(m, get_apps_dir())
            bar.update(1)

    return app_name


def get_app_path(app_name):
    return join(get_apps_dir(), app_name)


def make_run_script(run_config, run_script):
    idea_script = get_launch_script(run_config.path_to_app)

    with open(idea_script, 'r') as src, open(run_script, 'w') as dst:
        for line in src:
            if line.startswith("IDE_BIN_HOME"):
                line = f'IDE_BIN_HOME={join(run_config.path_to_app, "bin")}\n'
            elif line.find("classpath") != -1:
                line = f'  -classpath "$CLASSPATH:{PROJECTOR_SERVER_DIR}/*" \\\n'
            elif line.find(IDEA_PATH_SELECTOR) != -1:
                if run_config.ide_config_dir:
                    line = f'  -D{IDEA_PATH_SELECTOR}={run_config.ide_config_dir} \\\n'
            elif line.find(IDEA_RUN_CLASS) != -1:
                line = f'  -Dorg.jetbrains.projector.server.port={run_config.projector_port} \\\n'
                line += f'  -Dorg.jetbrains.projector.server.classToLaunch={IDEA_RUN_CLASS} \\\n'
                line += f'  {PROJECTOR_RUN_CLASS}\n'

            dst.write(line)

    st = stat(run_script)
    chmod(run_script, st.st_mode | 0o0111)


@dataclass()
class ProductInfo:
    name: str
    version: str
    build_number: str
    product_code: str
    data_dir: str
    svg_icon_path: str
    os: str
    launcher_path: str
    java_exec_path: str
    vm_options_path: str
    startup_wm_class: str


PRODUCT_INFO = 'product-info.json'


@dataclass()
class Version:
    year: int
    quart: int
    last: int


def parse_version(version):
    parsed = version.split(".")
    v = Version(int(parsed[0]), int(parsed[1]), int(parsed[2] if len(parsed) > 2 else -1))

    return v


def get_data_dir_from_script(run_script):
    with open(run_script, 'r') as f:
        for line in f:
            pos = line.find(IDEA_PATH_SELECTOR)

            if pos != -1:
                parts = line.split("=")

                if len(parts) < 2:
                    raise Exception(f"Unable to parse {IDEA_PATH_SELECTOR} line.")

                return parts[1].split(" ")[0]

    raise Exception("Unable to find data directory in the launch script.")


def get_product_info(app_path):
    prod_info_path = join(app_path, PRODUCT_INFO)
    with open(prod_info_path, "r") as f:
        data = json.load(f)

        pi = ProductInfo(data['name'], data['version'], data['buildNumber'],
                         data['productCode'], '', data['svgIconPath'],
                         data['launch'][0]['os'],
                         data['launch'][0]['launcherPath'],
                         data['launch'][0]['javaExecutablePath'],
                         data['launch'][0]['vmOptionsFilePath'],
                         data['launch'][0]['startupWmClass'])

        v = parse_version(pi.version)

        if v.year >= 2020 and v.quart >= 2:
            pi.data_dir = data['dataDirectoryName']
        else:
            pi.data_dir = get_data_dir_from_script(join(app_path, pi.launcher_path))

        return pi


def get_launch_script(app_path):
    prod_info = get_product_info(app_path)
    return join(app_path, prod_info.launcher_path)


CONFIG_PREFIX = expanduser('~/')
VER_2020_CONFIG_PREFIX = expanduser('~/.config/JetBrains')


def get_config_dir(app_path):
    pi = get_product_info(app_path)
    v = parse_version(pi.version)

    if v.year >= 2020:
        return join(VER_2020_CONFIG_PREFIX, pi.data_dir)

    return join(join(CONFIG_PREFIX, '.' + pi.data_dir), 'config')


PLUGIN_2020_PREFIX = expanduser('~/.local/share/JetBrains')


def get_plugin_dir(app_path):
    pi = get_product_info(app_path)
    v = parse_version(pi.version)

    if v.year >= 2020:
        return join(PLUGIN_2020_PREFIX, pi.data_dir)

    return join(get_config_dir(app_path), "plugins")
