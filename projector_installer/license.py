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

"""License related functions."""

import sys
import subprocess
import click

from .global_config import get_path_to_license


def display_license():
    """
    Displays the license and asks the user to accept it.
    Exits the program if the license is not accepted.
    """
    license_file = get_path_to_license()

    subprocess.run(
        ['less', '-P Please read the license. Up/Down/Space - scroll, q - finish reading. ',
         license_file], check=False)

    accept = click.prompt('Do you accept the license? [y/n]', type=bool)

    if not accept:
        click.echo('The license was not accepted, exiting...')
        sys.exit(2)
