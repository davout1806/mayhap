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
RE_WEIGHT = re.compile(r'\^((\d*\.)?\d+)$')

# Matches comments (lines starting with a hash)
# e.g. \t# hello world
RE_COMMENT = re.compile(r'\s*#.*')

# Matches integer ranges separated by a hyphen
# e.g. 10-20
RE_RANGE = re.compile(r'([+-]?\d+)\s*-\s*([+-]?\d+)')

# Matches variable definitions (variable name followed by equals and the value)
# e.g. _0varName= [symbol] pattern [2-5]
RE_VARIABLE_SET = re.compile(r'([a-zA-Z0-9_]+)\s*=\s*(.+)')

# Matches variable accesses (variable name preceded by $)
# e.g. $_0varName
RE_VARIABLE_GET = re.compile(r'\$([a-zA-z0-9_]+)')

BLOCK_START = '['
BLOCK_END = ']'


def parse_rule(rule):
    '''
    Parses an production rule into a weight and a production string.
    '''
    # Look for an explicit weight
    match = RE_WEIGHT.search(rule)
    if match:
        weight = float(match[1].strip())
        string_end = match.start()

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
    rule = random.choices(rules, weights)[0]
    return rule[1]


class MayhapGenerator:
    def __init__(self, grammar, verbose=False):
        self.grammar = grammar
        self.verbose = verbose
        self.variables = {}

    def log_pattern(self, pattern, depth=0):
        '''
        Log the given pattern to standard error, indented by its recursion
        depth for readability.
        '''
        if self.verbose:
            print(f'{"  " * depth}{pattern}', file=sys.stderr)

    def evaluate_block(self, block, depth=0):
        '''
        Expand the given block and return the final expanded string.
        '''
        self.log_pattern(f'[{block}]', depth)

        # Choose a item from the shortlist to produce
        shortlist = block.split('|')
        if len(shortlist) > 1:
            rules = [parse_rule(rule) for rule in shortlist]
            production = choose_production(rules)
            return self.evaluate_pattern(production, depth)

        block = block.strip()

        match = RE_RANGE.match(block)
        if match:
            bound1 = int(match[1])
            bound2 = int(match[2])
            lower = min(bound1, bound2)
            upper = max(bound1, bound2)
            choice = str(random.choice(range(lower, upper + 1)))
            self.log_pattern(choice, depth)
            return choice

        match = RE_VARIABLE_GET.match(block)
        if match:
            variable = match[1]
            value = self.variables[variable]
            self.log_pattern(value, depth)
            return value

        match = RE_VARIABLE_SET.match(block)
        if match:
            variable = match[1]
            value_pattern = match[2]
            value_production = self.evaluate_pattern(value_pattern, depth)
            self.variables[variable] = value_production
            return value_production

        # Substitute in a randomly chosen production of this symbol
        symbol = block
        rules = self.grammar[symbol]
        production = choose_production(rules)
        return self.evaluate_pattern(production, depth)

    def evaluate_pattern(self, pattern, depth=0):
        '''
        Expand all blocks in the given pattern and return the final expanded
        string.
        '''
        self.log_pattern(pattern, depth)

        stack = []
        i = 0
        while i < len(pattern):
            # If a block starts here, push its start index on the stack
            if pattern[i] == BLOCK_START:
                stack.append(i)

            # If a block ends here, pop its start index off the stack and
            # resolve it
            elif pattern[i] == BLOCK_END:
                start = stack.pop()
                end = i
                block = pattern[start + 1:end]
                production = self.evaluate_block(block, depth + 1)
                pattern = (pattern[:start] +
                           production +
                           pattern[end + 1:])

                self.log_pattern(pattern, depth)

                # Assume the production is fully resolved
                # Jump to the next unprocessed index
                i = start + len(production)
                continue

            i += 1

        return pattern

    def evaluate_input(self, pattern):
        '''
        Evaluate the given pattern as an input. If the pattern is the name of a
        symbol, expand and resolve it. Otherwise, evaluate the input as a
        pattern.
        '''
        # If a symbol name was given, expand it
        if pattern in self.grammar:
            pattern = choose_production(self.grammar[pattern])
            return self.evaluate_pattern(pattern)

        # Otherwise, interpret the input as a pattern
        return self.evaluate_pattern(pattern)


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

    generator = MayhapGenerator(grammar, args.verbose)

    # If a pattern was given, generate it and exit
    if args.pattern:
        print(generator.evaluate_input(args.pattern))
        return 0

    # Otherwise, read standard input
    try:
        for line in sys.stdin:
            print(generator.evaluate_input(line.strip()))
    except KeyboardInterrupt:
        # Quietly handle SIGINT, like cat does
        print()
        return 1

    return 0


if __name__ == '__main__':
    # Propagate return code
    sys.exit(main())
