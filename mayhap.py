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

import inflect


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
RE_RANGE = re.compile(r'([+-]?\d+)-([+-]?\d+)')

# Matches variable definitions (variable name followed by equals and the value)
# e.g. _0varName= [symbol] pattern [2-5]
RE_VARIABLE_SET = re.compile(r'([^\.]+)=([^\.]+)')

# Matches variable accesses (dollar sign followed by a variable name)
# e.g. $_0varName
RE_VARIABLE_GET = re.compile(r'\$([^\.]+)')

# Matches modifiers (period followed by a modifier type)
# e.g. .mundane
RE_MODIFIER = re.compile(r'\.([^\.]+)')

# Matches dynamic indefinite articles
# e.g. a(n)
RE_A = re.compile(r'(a)\((n)\)', re.IGNORECASE)

# Matches dynamic pluralization
# e.g. (s)
RE_S = re.compile(r'\((s)\)', re.IGNORECASE)

# The start and end of a block
# Must parse manually, as regular expressions cannot easily parse nested groups
BLOCK_START = '['
BLOCK_END = ']'

# Do not require a unique production to be chosen from the given symbol
MOD_MUNDANE = set(['mundane'])

# Add a context-sensitive indefinite article before this symbol
MOD_A = set(['a'])

# Pluralize this symbol
MOD_S = set(['s', 'plural', 'pluralForm'])

# Capitalize the first letter of the first word
MOD_CAPITALIZE = set(['capitalize'])

# Convert to lowercase
MOD_LOWER = set(['lower', 'lowerCase'])

# Convert to upper case
MOD_UPPER = set(['upper', 'upperCase'])

# Convert to title case (capitalize the first letter of each word)
MOD_TITLE = set(['title', 'titleCase'])

INFLECT_ENGINE = inflect.engine()


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
            weight = 1.0
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
        line = line.strip()
        if line:
            # Strip trailing comments
            match = RE_COMMENT.search(line)
            if match:
                line = line[:match.start(2)].strip()
                if not line:
                    continue

            match = RE_IMPORT.match(line)
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
                rule = Rule.parse(line)
                rule.production = rule.production.strip()
                grammar[current_symbol].add(rule)

            # Unindented lines contain symbols
            else:
                current_symbol = line
                grammar[current_symbol] = set()
    return grammar


def grammar_to_string(grammar):
    string = ''
    for symbol, rules in grammar.items():
        string += f'"{symbol}":\n'
        for rule in rules:
            string += f'\t{rule}\n'
    return string


def parse_modifiers(block):
    modifiers = []
    for match in RE_MODIFIER.finditer(block):
        # Slice block to get the symbol if this is the first match
        if not modifiers:
            symbol = block[:match.start()]
        modifiers.append(match[1])
    if not modifiers:
        symbol = block
    return symbol, modifiers


def has_modifier(modifier, modifiers):
    return not modifier.isdisjoint(set(modifiers))


def get_article(word):
    return INFLECT_ENGINE.a(word).split(' ')[0]


def resolve_indefinite_articles(pattern):
    output = ''
    last_match = 0
    for match in RE_A.finditer(pattern):
        output += pattern[last_match:match.start()]

        # Find the next word in the pattern
        next_word = ''
        for character in pattern[match.end() + 1:]:
            if not character.isalpha():
                break
            next_word += character

        if next_word:
            article = get_article(next_word)
        else:
            article = 'a'

        if match[1].isupper():
            article = article[0].upper() + article[1:]
        if match[2].isupper():
            article = article[0] + article[1:].upper()

        output += article

        last_match = match.end()
    output += pattern[last_match:]
    return output


def get_plural(word, number=None):
    if number is not None:
        return INFLECT_ENGINE.plural(word, number)
    return INFLECT_ENGINE.plural(word)


def resolve_plurals(pattern):
    output = ''
    last_match = 0
    for match in RE_S.finditer(pattern):
        # Find the previous number
        previous_word = ''
        previous_number = ''
        building_word = True
        for offset, character in enumerate(pattern[match.start() - 1::-1]):
            if building_word:
                if character.isalpha():
                    previous_word = character + previous_word
                    continue
                previous_word_start = match.start() - offset
                building_word = False
            if (character.isdigit() or
                    (previous_number and
                        character in '-.' and
                        previous_number[0] not in '-.')):
                previous_number = character + previous_number
            elif previous_number:
                break

        if previous_word:
            output += pattern[last_match:previous_word_start]

            if previous_number:
                if '.' in previous_number:
                    previous_number = float(previous_number)
                else:
                    previous_number = int(previous_number)

                previous_word = get_plural(previous_word, previous_number)
            else:
                previous_word = get_plural(previous_word)

            output += previous_word
        else:
            output += pattern[last_match:match.start()]
            output += match[1]

        last_match = match.end()
    output += pattern[last_match:]
    return output


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

        match = RE_VARIABLE_SET.match(block)
        if match:
            variable = match[1].strip()
            value_pattern = match[2].strip()
            value_production = self.evaluate_pattern(value_pattern, depth)
            self.variables[variable] = value_production
            return value_production

        symbol, modifiers = parse_modifiers(block)

        match = RE_VARIABLE_GET.match(block)
        if match:
            variable = match[1].strip()
            pattern = self.variables[variable]
        else:
            # Substitute in a randomly chosen production of this symbol
            unique = not has_modifier(MOD_MUNDANE, modifiers)
            rule = self.produce(symbol, unique)
            pattern = self.evaluate_pattern(rule.production, depth)

        for modifier in modifiers:
            if modifier in MOD_S:
                pattern = get_plural(pattern)
            elif modifier in MOD_A:
                pattern = get_article(pattern) + pattern
            elif modifier in MOD_CAPITALIZE:
                pattern = pattern.capitalize()
            elif modifier in MOD_LOWER:
                pattern = pattern.lower()
            elif modifier in MOD_UPPER:
                pattern = pattern.upper()
            elif modifier in MOD_TITLE:
                pattern = pattern.title()

        return pattern

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

        pattern = resolve_indefinite_articles(pattern)
        pattern = resolve_plurals(pattern)
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
