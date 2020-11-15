#  Copyright 2000-2020 JetBrains s.r.o.
#  Use of this source code is governed by the Apache 2.0 license that can be found
#  in the LICENSE file.

"""Check updates module"""

from distutils.version import LooseVersion
import socket
from typing import Optional, Any
from urllib.error import URLError

from .utils import get_json

from .version import __version__

PYPI_PRODUCT_URL = 'https://pypi.org/pypi/projector-installer/json'
LONG_NETWORK_TIMEOUT = 3.0
SHORT_NETWORK_TIMEOUT = 0.2


def get_latest_installer_version(timeout: float) -> Optional[Any]:
    """Retrieve projector-installer version from pypi with given timeout"""
    try:
        res = get_json(PYPI_PRODUCT_URL, timeout=timeout)
        return res['info']['version']
    except (URLError, socket.timeout):
        return None


def is_newer_than_current(ver_to_check: str) -> bool:
    """
    Compares given version with current.
    Returns True if given version is more recent
    """
    current_version = LooseVersion(__version__)
    pypi_version = LooseVersion(ver_to_check)
    return current_version < pypi_version


def is_update_available() -> bool:
    """Returns true if new projector-installer version
    is available on pypi
    """
    pypi_ver = get_latest_installer_version(LONG_NETWORK_TIMEOUT)

    if pypi_ver is None:
        return False

    return is_newer_than_current(pypi_ver)
