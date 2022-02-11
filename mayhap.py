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


# Matches a number preceded by a caret at the end of the line
# e.g. ^4.25
RE_WEIGHT = re.compile(r'\^(([0-9]*\.)?[0-9]+)$')

# Matches square blocks (paired brackets)
# e.g. [symbol]
# e.g. [symbol.pluralForm.upperCase]
RE_SQUARE = re.compile(r'\[(.+?)\]')

# Matches curly blocks (paired braces)
# e.g. {s}
# e.g. {option 1^2|5-9|[symbol]}
RE_CURLY = re.compile(r'\{(.+?)\}')


def parse_rule(rule):
    '''
    Parses an production rule into a weight and a production string.
    '''
    # Look for an explicit weight
    weight_match = RE_WEIGHT.search(rule)
    if weight_match is not None:
        weight = float(weight_match[1].strip())
        string_end = weight_match.start()

    # Default to 1 weight otherwise
    else:
        weight = 1
        string_end = len(rule)

    production = rule[:string_end]
    return weight, production


def parse_grammar(grammar_file):
    '''
    Parse the grammar in the given file as a dictionary mapping symbols to
    lists of weighted production rules. Assumes the file is open (as is the
    case for TextIOWrappers generated from argparse arguments).
    '''
    current_symbol = None
    grammar = {}
    for line in grammar_file:
        stripped = line.strip()
        if stripped:
            # Ignore comments
            if len(line) >= 2 and line.strip()[:2] == '//':
                continue

            # Indented lines contain production rules
            if line[0].isspace():
                rule = stripped
                weight, production = parse_rule(rule)
                production = production.strip()
                grammar[current_symbol].append((weight, production))

            # Unindented lines contain symbols
            else:
                current_symbol = stripped
                grammar[current_symbol] = []
    return grammar


def choose_production(rules):
    '''
    Choose an production from the given weighted list of rules.
    '''
    weights = [rule[0] for rule in rules]
    productions = [rule[1] for rule in rules]
    return random.choices(productions, weights)[0]


def log_pattern(pattern, depth=0):
    print(f'{"  " * depth}{pattern}', file=sys.stderr)


def evaluate_pattern(grammar, pattern, verbose=False, depth=0):
    '''
    Expand all expressions in the given pattern based on the given grammar and
    return the final expanded string.
    '''
    if verbose:
        log_pattern(pattern, depth)

    # Expand all shortlists
    match = RE_CURLY.search(pattern)
    while match:
        if verbose:
            log_pattern(match[0], depth + 1)

        block = match[1]

        # Choose a item from the shortlist to produce
        shortlist = block.split('|')
        rules = [parse_rule(rule) for rule in shortlist]
        production = choose_production(rules)
        production = evaluate_pattern(grammar, production, verbose, depth + 1)

        pattern = (pattern[:match.start()] +
                   production +
                   pattern[match.end():])

        if verbose:
            log_pattern(pattern, depth)
        match = RE_CURLY.search(pattern)

    # Expand all symbols
    match = RE_SQUARE.search(pattern)
    while match:
        if verbose:
            log_pattern(match[0], depth + 1)

        block = match[1].strip()

        # Substitute in a randomly chosen production of this symbol
        rules = grammar[block]
        production = choose_production(rules)
        production = evaluate_pattern(grammar, production, verbose, depth + 1)

        pattern = (pattern[:match.start()] +
                   production +
                   pattern[match.end():])

        if verbose:
            log_pattern(pattern, depth)
        match = RE_SQUARE.search(pattern)

    return pattern


def evaluate_input(grammar, pattern, verbose=False):
    # If a symbol name was given, expand it
    if pattern in grammar:
        pattern = choose_production(grammar[pattern])
        return evaluate_pattern(grammar, pattern, verbose)

    # Otherwise, interpret the input as a pattern
    return evaluate_pattern(grammar, pattern, verbose)


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

    grammar = parse_grammar(args.grammar)
    if args.verbose:
        dump = json.dumps(grammar, indent=4)
        print(f'Parsed grammar:\n{dump}\n', file=sys.stderr)

    # If a pattern was given, generate it and exit
    if args.pattern:
        print(evaluate_input(grammar, args.pattern, args.verbose))
        return 0

    # Otherwise, read standard input
    try:
        for line in sys.stdin:
            print(evaluate_input(grammar, line.strip(), args.verbose))
    except KeyboardInterrupt:
        # Quietly handle SIGINT, like cat does
        print()
        return 1

    return 0


if __name__ == '__main__':
    # Propagate return code
    sys.exit(main())
