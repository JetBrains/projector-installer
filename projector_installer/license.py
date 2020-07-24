# Copyright 2000-2020 JetBrains s.r.o.
# Use of this source code is governed by the Apache 2.0 license that can be found
# in the LICENSE file.


"""License related functions."""

import sys
import subprocess
import click

from .global_config import get_path_to_license


def display_license() -> None:
    """
    Displays the license and asks the user to accept it.
    Exits the program if the license is not accepted.
    """
    license_file = get_path_to_license()

    subprocess.run(
        ['less', '-P Please read the license. Up/Down/Space - scroll, q - finish reading. ',
         license_file], check=False)

    accept = click.prompt('This software includes components licensed under GPLv2. Do you accept '
                          'this license? [y/n]', type=bool)

    if not accept:
        click.echo('The license was not accepted, exiting...')
        sys.exit(2)
