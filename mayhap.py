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
RE_WEIGHT = re.compile(r'\^((\d*\.)?\d+)\s*$')

# Matches comments (lines starting with a hash)
# e.g. \t# hello world
RE_COMMENT = re.compile(r'(^|[^\\])(#.*)')

# Matches ranges separated by a hyphen
# e.g. 10-20
RE_RANGE_NUMERIC = re.compile(r'([+-]?\d+)-([+-]?\d+)')
# e.g. a-z
RE_RANGE_ALPHA = re.compile(r'([a-zA-Z])-([a-zA-Z])')

# Matches echoed variable assignments (variable name followed by equals and the
# value)
# e.g. _0varName= [symbol] pattern [2-5]
RE_ASSIGNMENT_ECHOED = re.compile(r'([^\.]+)=([^\.]+)')

# Matches silent variable assignments (variable name followed by tilda equals
# and the value)
# e.g. _0varName= [symbol] pattern [2-5]
RE_ASSIGNMENT_SILENT = re.compile(r'([^\.]+)~=([^\.]+)')

# Matches variable accesses (dollar sign followed by a variable name)
# e.g. $_0varName
RE_VARIABLE = re.compile(r'\$([^\.]+)')

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
PATTERN_START = '"'
PATTERN_END = '"'
LITERAL_START = "'"
LITERAL_END = "'"

# Do not require a unique production to be chosen from the given symbol
MOD_MUNDANE = 'mundane'

# Add a context-sensitive indefinite article before this symbol
MOD_A = 'a'

# Pluralize this symbol
MOD_S = 's'

# Capitalize the first letter of the first word
MOD_CAPITALIZE = 'capitalize'

# Convert to lowercase
MOD_LOWER = 'lower'

# Convert to upper case
MOD_UPPER = 'upper'

# Convert to title case (capitalize the first letter of each word)
MOD_TITLE = 'title'

# The default weight for rules with no explicit weight
DEFAULT_WEIGHT = 1.0

INFLECT_ENGINE = inflect.engine()


def join_as_strings(objects, delimiter=''):
    # For extreme debugging, change str(obj) to repr(obj)
    return delimiter.join([str(obj) for obj in objects])


class Token:
    pass


class LiteralToken(Token):
    def __init__(self, string, modifiers):
        self.string = string
        self.modifiers = modifiers

    def __str__(self):
        string_term = f"'{self.string}'"
        terms = [string_term] + self.modifiers
        return f"[{'.'.join(terms)}]"

    def __repr__(self):
        return (f'LiteralToken(string={repr(self.string)}, '
                f'modifiers={self.modifiers})')


class RangeToken(Token):
    def __init__(self, range_value, char, modifiers):
        self.range = range_value
        self.char = char
        self.modifiers = modifiers

    @property
    def start(self):
        if self.char:
            return chr(self.range.start)
        return self.range.start

    @property
    def stop(self):
        if self.char:
            return chr(self.range.stop - 1)
        return self.range.stop - 1

    def __str__(self):
        range_term = f'{self.start}-{self.stop}'
        terms = [range_term] + self.modifiers
        return f"[{'.'.join(terms)}]"

    def __repr__(self):
        return (f'RangeToken(range={self.range}, '
                f'modifiers={self.modifiers})')


class SymbolToken(Token):
    def __init__(self, symbol, modifiers):
        self.symbol = symbol
        self.modifiers = modifiers

    def __str__(self):
        symbol_term = join_as_strings(self.symbol)
        terms = [symbol_term] + self.modifiers
        return f"[{'.'.join(terms)}]"

    def __repr__(self):
        return (f'SymbolToken(symbol={self.symbol}, '
                f'modifiers={self.modifiers})')


class VariableToken(Token):
    def __init__(self, variable, modifiers):
        self.variable = variable
        self.modifiers = modifiers

    def __str__(self):
        return f'[${join_as_strings(self.variable)}]'

    def __repr__(self):
        return (f'VariableToken(variable={self.variable}, '
                f'modifiers={self.modifiers})')


class AssignmentToken(Token):
    def __init__(self, variable, value, echo):
        self.variable = variable
        self.value = value
        self.echo = echo

    def __str__(self):
        operator = '=' if self.echo else '~='
        return (f'[{join_as_strings(self.variable)}{operator}'
                f'{join_as_strings(self.value)}]')

    def __repr__(self):
        return (f'AssignmentToken(variable={self.variable}, '
                f'value={self.value}, '
                f'echo={self.echo})')


class ChoiceToken(Token):
    def __init__(self, rules):
        self.rules = rules

    def __str__(self):
        return f'[{join_as_strings(self.rules, delimiter="|")}]'

    def __repr__(self):
        return f'ChoiceToken(rules={self.rules})'


def parse_modifiers(block):
    modifiers = []
    for match in RE_MODIFIER.finditer(block):
        # Slice block to get its content if this is the first match
        if not modifiers:
            content = block[:match.start()]
        modifiers.append(match[1])
    if not modifiers:
        content = block
    return content, modifiers


def tokenize_pattern(pattern):
    tokens = []
    stack = []
    literal_start = 0
    i = 0
    while i < len(pattern):
        # If a block starts here, push its start index on the stack
        if pattern[i] == BLOCK_START:
            # If is top-level block, add the literal that was just traversed
            if not stack and i != literal_start:
                tokens.append(pattern[literal_start:i])
            stack.append(i)

        # If a block ends here, pop its start index off the stack
        elif pattern[i] == BLOCK_END:
            start = stack.pop()
            # If this is a top-level block, tokenize it
            if not stack:
                end = i
                block_pattern = pattern[start + 1:end]
                block_tokens = tokenize_block(block_pattern)
                for token in block_tokens:
                    tokens.append(token)
                literal_start = i + 1

        i += 1
    if i != literal_start:
        tokens.append(pattern[literal_start:i])
    return tokens


def tokenize_block(block):
    if not block:
        return Token()

    if (len(block) >= 2 and
            block[0] == LITERAL_START and
            block[-1] == LITERAL_END):
        if len(block) == 2:
            return []
        return [block[1:-1]]

    choices = block.split('|')
    if len(choices) > 1:
        rules = [Rule.parse(rule) for rule in choices]
        return [ChoiceToken(rules)]

    if (len(block) >= 2 and
            block[0] == PATTERN_START and
            block[-1] == PATTERN_START):
        if len(block) == 2:
            return []
        return tokenize_pattern(block[1:-1])

    assignment = False
    match = RE_ASSIGNMENT_SILENT.match(block)
    if match:
        assignment = True
        echo = False
    else:
        match = RE_ASSIGNMENT_ECHOED.match(block)
        if match:
            assignment = True
            echo = True

    if assignment:
        variable_pattern = match[1].strip()
        variable_tokens = tokenize_pattern(variable_pattern)
        value_block = match[2].strip()
        value_tokens = tokenize_block(value_block)
        return [AssignmentToken(variable_tokens, value_tokens, echo)]

    block = block.strip()
    content, modifiers = parse_modifiers(block)

    match = RE_RANGE_NUMERIC.match(content)
    is_range = False
    if match:
        is_range = True
        char = False
        bound1 = int(match[1])
        bound2 = int(match[2])
    else:
        match = RE_RANGE_ALPHA.match(content)
        if match:
            is_range = True
            char = True
            assert match[1].isupper() == match[2].isupper()
            bound1 = ord(match[1])
            bound2 = ord(match[2])

    if is_range:
        start = min(bound1, bound2)
        stop = max(bound1, bound2) + 1
        token_range = range(start, stop)
        return [RangeToken(token_range, char, modifiers)]

    match = RE_VARIABLE.match(content)
    if match:
        variable_pattern = match[1].strip()
        variable_tokens = tokenize_pattern(variable_pattern)
        return [VariableToken(variable_tokens, modifiers)]

    # Assume this is a symbol
    symbol_pattern = content
    symbol_tokens = tokenize_pattern(symbol_pattern)
    return [SymbolToken(symbol_tokens, modifiers)]


class Rule:
    def __init__(self, tokens, weight):
        self.tokens = tokens
        self.weight = weight

    @staticmethod
    def parse(rule, strip=False):
        '''
        Parses an production rule into a weight and a production string.
        '''
        # Look for an explicit weight
        match = RE_WEIGHT.search(rule)
        if match:
            weight = float(match[1])
            string_end = match.start()

        # Default to 1 weight otherwise
        else:
            weight = DEFAULT_WEIGHT
            string_end = len(rule)

        pattern = rule[:string_end]
        if strip:
            pattern = pattern.strip()
        tokens = tokenize_pattern(pattern)
        return Rule(tokens, weight)

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
        return f'{join_as_strings(self.tokens)}^{self.weight}'

    def __repr__(self):
        return f'Rule(tokens={self.tokens}, weight={self.weight})'


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
                rule = Rule.parse(stripped, strip=True)
                grammar[current_symbol].add(rule)

            # Unindented lines contain symbols
            else:
                current_symbol = stripped
                grammar[current_symbol] = set()
    return grammar


def grammar_to_string(grammar):
    string = ''
    for symbol, rules in grammar.items():
        string += f'{symbol}\n'
        for rule in rules:
            string += f'\t{rule}\n'
    return string


def get_article(word):
    return INFLECT_ENGINE.a(word).split(' ')[0]


def add_article(word):
    return INFLECT_ENGINE.a(word)


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
            # TODO consider throwing an error (or logging a warning) if symbols
            # must be reused
            if len(self.unused[symbol]) == 0:
                self.unused[symbol] = self.grammar[symbol].copy()

            rule = Rule.choose(self.unused[symbol])
            self.unused[symbol].remove(rule)
            return rule

        rule = Rule.choose(self.grammar[symbol])
        if rule in self.unused[symbol]:
            self.unused[symbol].remove(rule)
        return rule

    def log(self, string='', tokens=None, depth=0):
        '''
        Log the given pattern to standard error, indented by its recursion
        depth for readability.
        '''
        if self.verbose:
            if tokens is None:
                tokens = []
            print(f'{"  " * depth}{string}{join_as_strings(tokens)}',
                  file=sys.stderr)

    def evaluate_token(self, token, depth=0):
        if isinstance(token, str):
            return token

        self.log(tokens=[token], depth=depth)

        if isinstance(token, ChoiceToken):
            rule = Rule.choose(token.rules)
            return self.evaluate_tokens(rule.tokens, depth=depth + 1)

        if isinstance(token, AssignmentToken):
            variable = self.evaluate_tokens(token.variable, depth=depth + 1)
            value = self.evaluate_tokens(token.value, depth=depth + 1)
            self.log(tokens=[AssignmentToken(variable, value, token.echo)],
                     depth=depth)
            self.variables[variable] = value
            return value if token.echo else ''

        if isinstance(token, LiteralToken):
            string = token.string
        elif isinstance(token, RangeToken):
            choice = random.choice(token.range)
            if token.char:
                string = chr(choice)
            else:
                string = str(choice)
        elif isinstance(token, SymbolToken):
            symbol = self.evaluate_tokens(token.symbol, depth=depth + 1)
            rule = self.produce(symbol)
            string = self.evaluate_tokens(rule.tokens, depth=depth + 1)
        elif isinstance(token, VariableToken):
            variable = self.evaluate_tokens(token.variable, depth=depth + 1)
            value = self.variables[variable]
            string = value

        if token.modifiers:
            self.log(tokens=[LiteralToken(string, token.modifiers)],
                     depth=depth)
            for modifier in token.modifiers:
                if modifier in MOD_S:
                    string = get_plural(string)
                elif modifier in MOD_A:
                    string = add_article(string)
                elif modifier in MOD_CAPITALIZE:
                    string = string.capitalize()
                elif modifier in MOD_LOWER:
                    string = string.lower()
                elif modifier in MOD_UPPER:
                    string = string.upper()
                elif modifier in MOD_TITLE:
                    string = string.title()

        self.log(string=string, depth=depth)

        return string

    def evaluate_tokens(self, tokens, depth=0):
        string = ''

        for i, token in enumerate(tokens):
            if isinstance(token, str):
                string += token
            else:
                self.log(string=string, tokens=tokens[i:], depth=depth)
                string += self.evaluate_token(token, depth=depth + 1)

        if len(tokens) > 1:
            self.log(string=string, depth=depth)
        prev_string = string

        string = resolve_indefinite_articles(string)
        string = resolve_plurals(string)

        if string != prev_string:
            self.log(string=string, depth=depth)

        return string

    def evaluate_input(self, pattern):
        '''
        Evaluate the given pattern as an input. If the pattern is the name of a
        symbol, expand and resolve it. Otherwise, evaluate the input as a
        pattern.
        '''
        # If a symbol name was given, expand it
        if pattern in self.grammar:
            rule = self.produce(pattern)
            string = self.evaluate_tokens(rule.tokens)
            return string

        # Otherwise, interpret the input as a pattern
        tokens = tokenize_pattern(pattern)
        string = self.evaluate_tokens(tokens)
        return string


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
