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

RE_COMMENT = re.compile(r'\s*//.*')

BLOCK_START = '['
BLOCK_END = ']'


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
            if RE_COMMENT.match(stripped):
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
    '''
    Log the given pattern to standard error, indented by its recursion depth
    for readability.
    '''
    print(f'{"  " * depth}{pattern}', file=sys.stderr)


def evaluate_block(grammar, block, verbose=False, depth=0):
    '''
    Expand the given block based on the given grammar and return the final
    expanded string.
    '''
    if verbose:
        log_pattern(f'[{block}]', depth)

    # Choose a item from the shortlist to produce
    shortlist = block.split('|')
    if len(shortlist) > 1:
        rules = [parse_rule(rule) for rule in shortlist]
        production = choose_production(rules)
        return evaluate_pattern(grammar, production, verbose, depth)

    # Substitute in a randomly chosen production of this symbol
    symbol = block
    rules = grammar[symbol]
    production = choose_production(rules)
    return evaluate_pattern(grammar, production, verbose, depth)


def evaluate_pattern(grammar, pattern, verbose=False, depth=0):
    '''
    Expand all blocks in the given pattern based on the given grammar and
    return the final expanded string.
    '''
    if verbose:
        log_pattern(pattern, depth)

    stack = []
    i = 0
    while i < len(pattern):
        # If a block starts here, push its start index on the stack
        if pattern[i] == BLOCK_START:
            stack.append(i)

        # If a block ends here, pop its start index off the stack and resolve
        elif pattern[i] == BLOCK_END:
            start = stack.pop()
            end = i
            block = pattern[start + 1:end]
            production = evaluate_block(grammar, block, verbose, depth + 1)
            pattern = (pattern[:start] +
                       production +
                       pattern[end + 1:])

            if verbose:
                log_pattern(pattern, depth)

            # Assume the production is fully resolved
            # Jump to the next unprocessed index
            i = start + len(production)
            continue

        i += 1

    return pattern


def evaluate_input(grammar, pattern, verbose=False):
    '''
    Evaluate the given pattern as an input. If the pattern is the name of a
    symbol, expand and resolve it. Otherwise, evaluate the input as a pattern.
    '''
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
        print(f'Parsed grammar:\n{dump}', file=sys.stderr)

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
