# Mayhap - A grammar-based random text generator, inspired by Perchance
# Copyright (C) 2022 Aaron Friesen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from sys import stderr
from traceback import format_exc


def join_as_strings(objects, delimiter=''):
    # For extreme debugging, change str(obj) to repr(obj)
    return delimiter.join([str(obj) for obj in objects])


def print_error(e, verbose=True):
    if verbose:
        print(format_exc(), file=stderr)
    else:
        print(f'ERROR: {e}', file=stderr)


class MayhapError(Exception):
    pass


class MayhapGrammarError(MayhapError):
    def __init__(self, message, number, line):
        super().__init__()
        self.message = message
        self.number = number
        self.line = line

    def print(self):
        print(f'ERROR (line {self.number}): {self.message}', file=stderr)
        print(self.line, file=stderr)
