#  Copyright 2000-2021 JetBrains s.r.o.
#  Use of this source code is governed by the Apache 2.0 license that can be found
#  in the LICENSE file.

"""IDE update stuff"""
from distutils.version import LooseVersion
from typing import Optional, List

import click

from .config_generator import save_config
from .products import Product, get_product_releases, IDEKind, init_compatible_apps
from .apps import is_projector_installed_ide, get_product_info, download_and_install
from .run_config import RunConfig

CODE2KIND = {
    'IC': IDEKind.Idea_Community,
    'IU': IDEKind.Idea_Ultimate,
    'PC': IDEKind.PyCharm_Community,
    'PY': IDEKind.PyCharm_Professional,
    'CL': IDEKind.CLion,
    'GO': IDEKind.GoLand,
    'DB': IDEKind.DataGrip,
    'PS': IDEKind.PhpStorm,
    'WS': IDEKind.WebStorm,
    'RM': IDEKind.RubyMine,
}


def is_updatable_ide(path_to_ide: str) -> bool:
    """Returns true if IDE updatable"""
    return is_projector_installed_ide(path_to_ide)


def get_product_list_from_file(kind: IDEKind) -> List[Product]:
    """Get product list from compatible IDE json"""
    return [prod for prod in init_compatible_apps() if prod.kind == kind]


def is_tested_ide(path_to_ide: str) -> bool:
    """Returns True if given IDE is from compatible list"""
    prod_info = get_product_info(path_to_ide)
    kind: IDEKind = CODE2KIND.get(prod_info.product_code, IDEKind.Unknown)
    ver = LooseVersion(prod_info.version)

    for prod in init_compatible_apps():
        if prod.kind == kind and prod.ver == ver:
            return True

    return False


def get_update(path_to_ide: str) -> Optional[Product]:
    """Returns update for given app if available"""
    prod_info = get_product_info(path_to_ide)
    kind: IDEKind = CODE2KIND.get(prod_info.product_code, IDEKind.Unknown)

    if kind == IDEKind.Unknown:
        return None

    current = LooseVersion(prod_info.version)

    prod_list = get_product_list_from_file(kind) \
        if is_tested_ide(path_to_ide) else get_product_releases(kind)

    product = None

    for prod in prod_list:
        if prod.ver > current and (product is None or prod.ver > product.ver):
            product = prod

    return product


def update_config(run_config: RunConfig, product: Product) -> None:
    """Updates IDE in given config"""
    run_config.path_to_app = download_and_install(product.url)
    save_config(run_config)


def check_ide_update(run_config: RunConfig) -> None:
    """Check if update is available and prints message if yes"""
    if is_updatable_ide(run_config.path_to_app):
        product = get_update(run_config.path_to_app)

        if product is not None:
            msg = f'\nNew version {product.name} is available. ' \
                  f'To update use command: projector config update {run_config.name}\n'
            click.echo(click.style(msg, bold=True))
