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
    lists of weighted expansion rules. Assumes the file is open (as is the case
    for TextIOWrappers generated from argparse arguments).
    '''
    # Matches a number preceded by a caret at the end of the line
    # e.g. ^4.25
    weight_re = re.compile(r'\s*\^(([0-9]*[.])?[0-9]+)$')

    # Parse the given file line-by-line
    current = None
    grammar = {}
    for line in grammar_file:
        if line.strip():
            # Ignore comments
            if len(line) >= 2 and line.strip()[:2] == '//':
                continue

            # Indented lines contain expansion rules
            if line[0].isspace():
                expansion = line.strip()

                # Look for an explicit weight
                weight_match = weight_re.search(expansion)
                if weight_match is not None:
                    weight = float(weight_match[1].strip())
                    string_end = weight_match.start()

                # Default to 1 weight otherwise
                else:
                    weight = 1
                    string_end = len(expansion)

                grammar[current].append((weight, expansion[:string_end]))

            # Unindented lines contain symbols
            else:
                symbol = line.strip()
                current = symbol
                grammar[symbol] = []
    return grammar


def choose(expansions):
    '''
    Choose an expansion from the given weighted list of expansions.
    '''
    weights = [expansion[0] for expansion in expansions]
    strings = [expansion[1] for expansion in expansions]
    return random.choices(strings, weights)[0]


def generate(grammar, pattern, verbose=False, depth=0):
    '''
    Expand all expressions in the given pattern based on the given grammar and
    return the final expanded string.
    '''
    if verbose:
        print(f'{"  " * depth}{pattern}', file=sys.stderr)

    # Matches bracketed symbols
    # e.g. [symbol]
    nonterminal = re.compile(r'\[(.+?)\]')

    # Matches shorthand lists in braces
    # e.g. {option 1|option 2|[symbol]}
    shorthand = re.compile(r'\{(.+?)\}')

    # Expand all shorthand lists
    match = shorthand.search(pattern)
    while match:
        expansions = match[1].split('|')
        expansion = random.choice(expansions)
        pattern = (pattern[:match.start()] +
                   expansion +
                   pattern[match.end():])

        if verbose:
            print(f'{"  " * depth}{pattern}', file=sys.stderr)
        match = shorthand.search(pattern)

    # Expand all bracketed nonterminal symbols
    match = nonterminal.search(pattern)
    while match:
        # Substitute in a randomly chosen expansion of this symbol
        symbol = match[1]
        expansion = choose(grammar[symbol])
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
                pattern = choose(grammar[line])
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
