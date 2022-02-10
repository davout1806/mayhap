#!/usr/bin/env python3
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

from argparse import ArgumentParser, FileType
import json
import random
import re
import sys


def parse(grammar_file):
    '''
    Parse the grammar in the given file as a dictionary mapping symbols to
    lists of expansion rules. Assumes the file is open (as is the case for
    TextIOWrappers generated from argparse arguments).
    '''
    current = None
    grammar = {}
    for line in grammar_file:
        if line.strip():
            # Ignore comments
            if len(line) >= 2 and line.strip()[:2] == '//':
                continue

            # Indented lines contain expansion rules
            if line[0].isspace():
                grammar[current].append(line.strip())

            # Unindented lines contain symbols
            else:
                current = line.strip()
                grammar[current] = []
    return grammar


def generate(grammar, pattern, verbose=False, depth=0):
    '''
    Expand all expressions in the given pattern based on the given grammar and
    return the final expanded string.
    '''
    if verbose:
        print(f'{"  " * depth}{pattern}', file=sys.stderr)

    # Expand all bracketed nonterminal symbols
    nonterminal = re.compile(r'\[([^\]]*)\]')
    match = nonterminal.search(pattern)
    while match:
        # Substitute in a randomly chosen expansion of this symbol
        symbol = match[1]
        expansion = random.choice(grammar[symbol])
        pattern = (pattern[:match.start()] +
                   generate(grammar, expansion, verbose, depth + 1) +
                   pattern[match.end():])

        if verbose:
            print(f'{"  " * depth}{pattern}', file=sys.stderr)
        match = nonterminal.search(pattern)

    return pattern


def main():
    '''
    Parse arguments and handle input and output.
    '''
    parser = ArgumentParser(description='A grammar-based random text '
                                        'generator, inspired by Perchance')
    parser.add_argument(
            'grammar',
            type=FileType('r'),
            help='file that defines the grammar to generate from')
    parser.add_argument(
            'pattern',
            nargs='?',
            help='the pattern to generate from the grammar; if this argument '
                 'is not provided, read from standard input instead')
    parser.add_argument(
            '-v', '--verbose',
            action='store_true',
            help='explain what is being done; extra messages are written to '
                 'stderr, so stdout is still clean')
    args = parser.parse_args()

    grammar = parse(args.grammar)
    if args.verbose:
        dump = json.dumps(grammar, indent=4)
        print(f'Parsed grammar:\n{dump}\n', file=sys.stderr)

    # If a pattern was given, generate it and exit
    if args.pattern:
        print(generate(grammar, args.pattern, args.verbose))
        return 0

    # Otherwise, read standard input
    try:
        for line in sys.stdin:
            line = line.strip()

            # If a symbol name was given, expand it
            if line in grammar:
                pattern = random.choice(grammar[line])
                print(generate(grammar, pattern, args.verbose))

            # Otherwise, interpret the input as a pattern
            else:
                print(generate(grammar, line, args.verbose))
    except KeyboardInterrupt:
        # Quietly handle SIGINT, like cat does
        print()
        return 1

    return 0


if __name__ == '__main__':
    # Propagate return code
    sys.exit(main())
