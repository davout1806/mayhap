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
from copy import deepcopy
from os import chdir
from os.path import dirname, isfile
import random
import re
import sys


# Matches the name of a generator to import when parsing a grammar
# e.g. @generator_name
# e.g. @/home/username/generator_name.mh
RE_IMPORT = re.compile(r'@(.+)')

# Matches a weight appended to a rule (a number preceded by a caret at the end
# of the line)
# e.g. ^4.25
RE_WEIGHT = re.compile(r'\^((\d*\.)?\d+)$')

# Matches comments (lines starting with a hash)
# e.g. \t# hello world
RE_COMMENT = re.compile(r'(^|[^\\])(#.*)')

# Matches integer ranges separated by a hyphen
# e.g. 10-20
RE_RANGE = re.compile(r'([+-]?\d+)\s*-\s*([+-]?\d+)')

# Matches variable definitions (variable name followed by equals and the value)
# e.g. _0varName= [symbol] pattern [2-5]
RE_VARIABLE_SET = re.compile(r'(.+?)\s*=\s*(.+)')

# Matches variable accesses (variable name preceded by $)
# e.g. $_0varName
RE_VARIABLE_GET = re.compile(r'\$(.+?)')

# Matches mundane symbols (symbol name followed by ?)
# e.g. symbol?
RE_MUNDANE = re.compile(r'(.+)\?')

BLOCK_START = '['
BLOCK_END = ']'


class Rule:
    def __init__(self, production, weight):
        self.production = production
        self.weight = weight

    @staticmethod
    def parse(rule):
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
        return Rule(production, weight)

    @staticmethod
    def choose(rules):
        '''
        Choose a production from the given weighted list of rules.
        '''
        rules_tuple = tuple(rules)
        weights = [rule.weight for rule in rules_tuple]
        rule = random.choices(rules_tuple, weights)[0]
        return rule

    def __str__(self):
        return f'"{self.production}" (weight {self.weight})'

    def __repr__(self):
        return f'Rule(production={self.production}, weight={self.weight})'


def parse_grammar(lines):
    current_symbol = None
    grammar = {}
    for line in lines:
        stripped = line.strip()
        if stripped:
            # Strip trailing comments
            match = RE_COMMENT.search(stripped)
            if match:
                stripped = stripped[:match.start(2)].strip()
                if not stripped:
                    continue

            match = RE_IMPORT.match(stripped)
            if match:
                import_file_name = match[1]
                # Default to .mh extension if not specified
                if not isfile(import_file_name):
                    import_file_name = f'{match[1]}.mh'
                with open(import_file_name) as import_file:
                    grammar |= parse_grammar(import_file)
                continue

            # Indented lines contain production rules
            if line[0].isspace():
                rule = Rule.parse(stripped)
                rule.production = rule.production.strip()
                grammar[current_symbol].add(rule)

            # Unindented lines contain symbols
            else:
                current_symbol = stripped
                grammar[current_symbol] = set()
    return grammar


def grammar_to_string(grammar):
    string = ''
    for symbol, rules in grammar.items():
        string += f'"{symbol}":\n'
        for rule in rules:
            string += f'\t{rule}\n'
    return string


class Generator:
    def __init__(self, grammar, verbose=False):
        self.grammar = grammar
        self.verbose = verbose
        self.variables = {}
        self.unused = deepcopy(self.grammar)

    def reset(self):
        self.variables = {}
        self.unused = deepcopy(self.grammar)

    def produce(self, symbol, unique=True):
        if unique:
            # If all symbols have been used, old symbols must be reused
            # Recreate and draw from the unused list again to reduce duplicates
            # TODO consider throwing an error if symbols must be reused
            if len(self.unused[symbol]) == 0:
                self.unused[symbol] = self.grammar[symbol].copy()

            rule = Rule.choose(self.unused[symbol])
            self.unused[symbol].remove(rule)
            return rule

        rule = Rule.choose(self.grammar[symbol])
        if rule in self.unused[symbol]:
            self.unused[symbol].remove(rule)
        return rule

    def log(self, string, block, depth=0):
        '''
        Log the given pattern to standard error, indented by its recursion
        depth for readability.
        '''
        if self.verbose:
            start = '[' if block else '"'
            end = ']' if block else '"'
            print(f'{"  " * depth}{start}{string}{end}', file=sys.stderr)

    def evaluate_block(self, block, depth=0):
        '''
        Expand the given block and return the final expanded string.
        '''
        self.log(block, block=True, depth=depth)

        # Choose a item from the shortlist to produce
        shortlist = block.split('|')
        if len(shortlist) > 1:
            rules = [Rule.parse(rule) for rule in shortlist]
            rule = Rule.choose(rules)
            return self.evaluate_pattern(rule.production, depth)

        block = block.strip()

        match = RE_RANGE.match(block)
        if match:
            bound1 = int(match[1])
            bound2 = int(match[2])
            lower = min(bound1, bound2)
            upper = max(bound1, bound2)
            choice = str(random.choice(range(lower, upper + 1)))
            self.log(choice, block=False, depth=depth)
            return choice

        match = RE_VARIABLE_GET.match(block)
        if match:
            variable = match[1]
            value = self.variables[variable]
            self.log(value, block=False, depth=depth)
            return value

        match = RE_VARIABLE_SET.match(block)
        if match:
            variable = match[1]
            value_pattern = match[2]
            value_production = self.evaluate_pattern(value_pattern, depth)
            self.variables[variable] = value_production
            return value_production

        match = RE_MUNDANE.match(block)
        unique = not match
        symbol = match[1] if match else block

        # Substitute in a randomly chosen production of this symbol
        rule = self.produce(symbol, unique)
        return self.evaluate_pattern(rule.production, depth)

    def evaluate_pattern(self, pattern, depth=0):
        '''
        Expand all blocks in the given pattern and return the final expanded
        string.
        '''
        self.log(pattern, block=False, depth=depth)

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

                self.log(pattern, block=False, depth=depth)

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
            rule = self.produce(pattern)
            return self.evaluate_pattern(rule.production)

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

    # Change working directory to directory containing the given grammar
    # This allows for import paths relative to the given grammar
    chdir(dirname(args.grammar.name))
    grammar = parse_grammar(args.grammar)
    if args.verbose:
        print(grammar_to_string(grammar), file=sys.stderr)

    generator = Generator(grammar, args.verbose)

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
