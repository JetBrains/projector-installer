#  Copyright 2000-2020 JetBrains s.r.o.
#  Use of this source code is governed by the Apache 2.0 license that can be found
#  in the LICENSE file.

"""InstallableApp class and related stuff"""
import json
from typing import List, Tuple


class InstallableApp:
    """Installable application entry."""

    def __init__(self, name: str, url: str) -> None:
        self.name: str = name
        self.url: str = url

    def __key__(self) -> Tuple[str, str]:
        return self.name, self.url

    def __eq__(self, other: object) -> bool:
        if isinstance(other, InstallableApp):
            return self.__key__() == other.__key__()

        return False

    def __hash__(self) -> int:
        return hash(self.__key__())


def load_installable_apps(file_name: str) -> List[InstallableApp]:
    """Loads installable app list from json file."""
    with open(file_name, 'r') as file:
        data = json.load(file)

    return [InstallableApp(entry['name'], entry['url']) for entry in data]
