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
from cmd import Cmd
from copy import deepcopy
from os import chdir, isatty
from os.path import dirname, isfile
import random
import re
import sys
from sys import stderr, stdin
from traceback import format_exc
import typing

from pyparsing import (Combine,
                       Forward,
                       Literal,
                       OneOrMore,
                       Optional,
                       ParseException,
                       Suppress,
                       Word,
                       ZeroOrMore,
                       alphanums,
                       alphas,
                       nums,
                       printables,
                       remove_quotes,
                       sgl_quoted_string)

try:
    import inflect
    INFLECT: typing.Optional[inflect.engine] = inflect.engine()
except ImportError:
    INFLECT = None


class Token:
    pass


class LiteralToken(Token):
    def __init__(self, string, modifiers=None):
        self.string = string
        self.modifiers = tuple(modifiers) if modifiers else tuple()

    def __str__(self):
        string_term = f"'{self.string}'"
        terms = (string_term,) + self.modifiers
        return f"[{'.'.join(terms)}]"

    def __repr__(self):
        return (f'LiteralToken(string={repr(self.string)}, '
                f'modifiers={self.modifiers})')

    def __eq__(self, other):
        return (isinstance(other, LiteralToken) and
                self.string == other.string and
                self.modifiers == other.modifiers)

    def __hash__(self):
        return hash(self.string)


class PatternToken(Token):
    def __init__(self, tokens, modifiers=None):
        self.tokens = tuple(tokens)
        self.modifiers = tuple(modifiers) if modifiers else tuple()

    def __str__(self):
        token_term = f'"{join_as_strings(self.tokens)}"'
        terms = (token_term,) + self.modifiers
        return f"[{'.'.join(terms)}]"

    def __repr__(self):
        return (f'PatternToken(tokens={self.tokens}, '
                f'modifiers={self.modifiers})')

    def __eq__(self, other):
        return (isinstance(other, PatternToken) and
                self.tokens == other.tokens and
                self.modifiers == other.modifiers)

    def __hash__(self):
        return hash(self.tokens)


class RangeToken(Token):
    def __init__(self, range_value, alpha, modifiers=None):
        self.range = range_value
        self.alpha = alpha
        self.modifiers = tuple(modifiers) if modifiers else tuple()

    @property
    def start(self):
        if self.alpha:
            return chr(self.range.start)
        return self.range.start

    @property
    def stop(self):
        if self.alpha:
            return chr(self.range.stop - 1)
        return self.range.stop - 1

    def __str__(self):
        range_term = f'{self.start}-{self.stop}'
        terms = (range_term,) + self.modifiers
        return f"[{'.'.join(terms)}]"

    def __repr__(self):
        return (f'RangeToken(range={self.range}, '
                f'modifiers={self.modifiers})')

    def __eq__(self, other):
        return (isinstance(other, RangeToken) and
                self.range == other.range and
                self.alpha == other.alpha and
                self.modifiers == other.modifiers)

    def __hash__(self):
        return hash(self.range)


class SymbolToken(Token):
    def __init__(self, symbol, modifiers=None):
        self.symbol = symbol
        self.modifiers = tuple(modifiers) if modifiers else tuple()

    def __str__(self):
        symbol_term = join_as_strings(self.symbol)
        terms = (symbol_term,) + self.modifiers
        return f"[{'.'.join(terms)}]"

    def __repr__(self):
        return (f'SymbolToken(symbol="{self.symbol}", '
                f'modifiers={self.modifiers})')

    def __eq__(self, other):
        return (isinstance(other, SymbolToken) and
                self.symbol == other.symbol and
                self.modifiers == other.modifiers)

    def __hash__(self):
        return hash(self.symbol)


class VariableToken(Token):
    def __init__(self, variable, modifiers=None):
        self.variable = variable
        self.modifiers = tuple(modifiers) if modifiers else tuple()

    def __str__(self):
        return f'[${join_as_strings(self.variable)}]'

    def __repr__(self):
        return (f'VariableToken(variable="{self.variable}", '
                f'modifiers={self.modifiers})')

    def __eq__(self, other):
        return (isinstance(other, VariableToken) and
                self.variable == other.variable and
                self.modifiers == other.modifiers)

    def __hash__(self):
        return hash(self.variable)


class AssignmentToken(Token):
    def __init__(self, variable, value, echo):
        self.variable = variable
        self.value = tuple(value)
        self.echo = echo

    def __str__(self):
        operator = '=' if self.echo else '~'
        return (f'[{join_as_strings(self.variable)}{operator}'
                f'{join_as_strings(self.value)}]')

    def __repr__(self):
        return (f'AssignmentToken(variable={self.variable}, '
                f'value={self.value}, '
                f'echo={self.echo})')

    def __eq__(self, other):
        return (isinstance(other, AssignmentToken) and
                self.variable == other.variable and
                self.value == other.value and
                self.echo == other.echo)

    def __hash__(self):
        return hash((self.variable, self.value))


class ChoiceToken(Token):
    def __init__(self, rules):
        self.rules = tuple(rules)

    def __str__(self):
        return f'[{join_as_strings(self.rules, delimiter="|")}]'

    def __repr__(self):
        return f'ChoiceToken(rules={self.rules})'

    def __eq__(self, other):
        return (isinstance(other, ChoiceToken) and
                self.rules == other.rules)

    def __hash__(self):
        return hash(self.rules)


class Weight:
    def __init__(self, weight):
        self.weight = weight


def word_excluding(exclude_chars):
    return Word(printables + ' ',
                exclude_chars=exclude_chars).leave_whitespace()


def parse_literal(toks):
    return LiteralToken(toks[0])


def parse_pattern(toks):
    return PatternToken(tuple(toks))


def parse_range_num(toks):
    bound1 = int(toks[0])
    bound2 = int(toks[1])
    start = min(bound1, bound2)
    stop = max(bound1, bound2) + 1
    return RangeToken(range(start, stop), alpha=False)


def parse_range_alpha(toks):
    bound1 = ord(toks[0])
    bound2 = ord(toks[1])
    start = min(bound1, bound2)
    stop = max(bound1, bound2) + 1
    return RangeToken(range(start, stop), alpha=True)


def parse_symbol(toks):
    return SymbolToken(toks[0])


def parse_variable(toks):
    return VariableToken(toks[0])


def parse_assignment_echo(toks):
    return AssignmentToken(toks[0], tuple(toks[1:]), echo=True)


def parse_assignment_silent(toks):
    return AssignmentToken(toks[0], tuple(toks[1:]), echo=False)


def parse_choices(toks):
    rules = [(rule if rule else Rule([])) for rule in toks]
    return ChoiceToken(tuple(rules))


def parse_modifiers(toks):
    toks[0].modifiers = tuple(toks[1:])
    return toks[0]


def parse_weight(toks):
    return Weight(float(toks[0]))


def parse_rule(toks):
    if isinstance(toks[-1], Weight):
        return Rule(toks[:-1], toks[-1].weight)
    return Rule(toks)


# Parser expressions
E_NUMBER = Combine(Optional(Word(nums)) + '.' + Word(nums)) | Word(nums)
E_WEIGHT = Suppress('^') + E_NUMBER
E_WEIGHT.add_parse_action(parse_weight)

E_SPECIAL = Forward()

E_BLOCK = Suppress('[') + E_SPECIAL + Suppress(']')

E_UNQUOTED_TEXT = Combine(OneOrMore(word_excluding('"[]'))).leave_whitespace()
E_UNQUOTED_TOKEN = Forward()

E_LITERAL = sgl_quoted_string.set_parse_action(remove_quotes)
E_LITERAL.add_parse_action(parse_literal)

E_PATTERN = Suppress('"') + OneOrMore(E_UNQUOTED_TOKEN) + Suppress('"')
E_PATTERN.add_parse_action(parse_pattern)

E_RANGE_NUM = Word(nums) + Suppress('-') + Word(nums)
E_RANGE_NUM.add_parse_action(parse_range_num)

E_RANGE_ALPHA = Word(alphas, exact=1) + Suppress('-') + Word(alphas, exact=1)
E_RANGE_ALPHA.add_parse_action(parse_range_alpha)

E_RANGE = E_RANGE_NUM | E_RANGE_ALPHA

E_SYMBOL = Word(alphanums + '_')
E_SYMBOL.add_parse_action(parse_symbol)

E_VARIABLE_NAME = Word(alphanums + '_')
E_VARIABLE_ACCESS = Suppress('$') + E_VARIABLE_NAME
E_VARIABLE_ACCESS.add_parse_action(parse_variable)

E_ASSIGNMENT_ECHO = E_VARIABLE_NAME + Literal('=').suppress() + E_SPECIAL
E_ASSIGNMENT_ECHO.add_parse_action(parse_assignment_echo)
E_ASSIGNMENT_SILENT = E_VARIABLE_NAME + Literal('~').suppress() + E_SPECIAL
E_ASSIGNMENT_SILENT.add_parse_action(parse_assignment_silent)
E_ASSIGNMENT = E_ASSIGNMENT_ECHO | E_ASSIGNMENT_SILENT

E_RULE = Forward()
E_CHOICES = (Optional(E_RULE, default=None).leave_whitespace()
             + OneOrMore(Suppress('|')
                         + Optional(E_RULE, default=None).leave_whitespace()))
E_CHOICES.add_parse_action(parse_choices)

E_MODIFIER = Suppress('.') + Word(alphanums + '_')
E_MODDED = ((E_LITERAL | E_PATTERN | E_RANGE | E_SYMBOL | E_VARIABLE_ACCESS)
            + ZeroOrMore(E_MODIFIER))
E_MODDED.add_parse_action(parse_modifiers)

E_SPECIAL <<= E_ASSIGNMENT | E_CHOICES | E_MODDED

E_UNQUOTED_TOKEN <<= (E_UNQUOTED_TEXT | E_BLOCK).leave_whitespace()

E_TEXT = Combine(OneOrMore(word_excluding('|^[]'))).leave_whitespace()
E_TOKEN = (E_TEXT | E_BLOCK).leave_whitespace()

E_RULE <<= ZeroOrMore(E_TOKEN) + Optional(E_WEIGHT)
E_RULE.add_parse_action(parse_rule)


# Matches the name of a generator to import when parsing a grammar
# e.g. @generator_name
# e.g. @/home/username/generator_name.mh
RE_IMPORT = re.compile(r'@(.+)')

# Matches comments (lines starting with a hash)
# e.g. \t# hello world
RE_COMMENT = re.compile(r'(^|[^\\])(#.*)')

# Matches dynamic indefinite articles
# e.g. a(n)
RE_ARTICLE = re.compile(r'(a)\((n)\)', re.IGNORECASE)

# Matches dynamic pluralization
# e.g. (s)
RE_PLURAL = re.compile(r'\((s)\)', re.IGNORECASE)

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
MOD_ARTICLE = 'a'

# Pluralize this symbol
MOD_PLURAL = 's'

# Convert this number to an ordinal (e.g. 1st, 10th)
MOD_ORDINAL = 'th'

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

# The string that prefixes commands in interactive mode
# Non-command inputs are interpreted as patterns or symbols
COMMAND_PREFIX = '/'


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


class Rule:
    def __init__(self, tokens, weight=DEFAULT_WEIGHT):
        self.tokens = tuple(tokens)
        self.weight = weight

    @staticmethod
    def parse(rule):
        '''
        Parses an production rule into a weight and a production string.
        '''
        try:
            return E_RULE.parse_string(rule)[0]
        except ParseException as e:
            raise MayhapError('Error parsing rule: {e}') from e

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

    def __eq__(self, other):
        return (isinstance(other, Rule) and
                self.tokens == other.tokens and
                self.weight == other.weight)

    def __hash__(self):
        return hash(self.tokens)


def import_grammar(import_file_name):
    # Default to .mh extension if not specified
    if not isfile(import_file_name) and not import_file_name.endswith('.mh'):
        import_file_name = f'{import_file_name}.mh'
    try:
        with open(import_file_name) as import_file:
            try:
                return parse_grammar(import_file)
            except MayhapError as e:
                raise MayhapError('Error while importing grammar from '
                                  f'{import_file_name}: {e}') from e
    except (OSError) as e:
        raise MayhapError('Failed to import grammar from '
                          f'{import_file_name}: {e}') from e


def parse_grammar(lines):
    current_symbol = None
    grammar = {}
    for i, line in enumerate(lines):
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
                try:
                    grammar |= import_grammar(import_file_name)
                except MayhapError as e:
                    raise MayhapGrammarError(str(e), i + 1, line) from e
                continue

            # Indented lines contain production rules
            if line[0].isspace():
                if current_symbol is None:
                    raise MayhapGrammarError('Production rule given before '
                                             'symbol', i + 1, line)

                try:
                    rule = Rule.parse(stripped)
                except MayhapError as e:
                    raise MayhapGrammarError(str(e), i + 1, line) from e
                grammar[current_symbol].add(rule)

            # Unindented lines contain symbols
            else:
                if current_symbol and not grammar[current_symbol]:
                    raise MayhapGrammarError(f'Symbol "{current_symbol}" '
                                             'closed with no production rules',
                                             i + 1, line)

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
    if INFLECT:
        return INFLECT.a(word).split()[0]
    if word and word[0] in 'aeiou':
        return 'an'
    return 'a'


def add_article(word):
    if INFLECT:
        return INFLECT.a(word)
    return get_article(word) + ' ' + word


def resolve_indefinite_articles(pattern):
    output = ''
    last_match = 0
    for match in RE_ARTICLE.finditer(pattern):
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
    if INFLECT:
        if number is not None:
            return INFLECT.plural(word, number)
        return INFLECT.plural(word)
    if number is not None and number == 1:
        return word
    return word + 's'


def resolve_plurals(pattern):
    output = ''
    last_match = 0
    for match in RE_PLURAL.finditer(pattern):
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


def get_ordinal(number):
    if INFLECT:
        return INFLECT.ordinal(number)
    if number.isdigit():
        last_digit = int(number) % 10
        if last_digit == 1:
            return f'{number}st'
        if last_digit == 2:
            return f'{number}nd'
        if last_digit == 3:
            return f'{number}rd'
    return f'{number}th'


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
            rules = self.unused.get(symbol)
            if rules is None:
                raise MayhapError(f'Symbol "{symbol}" not found')

            if len(rules) == 0:
                self.unused[symbol] = self.grammar[symbol].copy()

            rule = Rule.choose(self.unused[symbol])
            self.unused[symbol].remove(rule)
            return rule

        rules = self.grammar[symbol]
        if rules is None:
            raise MayhapError(f'Symbol "{symbol}" not found')
        rule = Rule.choose(rules)
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
                  file=stderr)

    def evaluate_token(self, token, depth=0):
        if isinstance(token, str):
            return token

        self.log(tokens=[token], depth=depth)

        if isinstance(token, ChoiceToken):
            rule = Rule.choose(token.rules)
            return self.evaluate_tokens(rule.tokens, depth=depth + 1)

        if isinstance(token, AssignmentToken):
            variable = token.variable
            value = self.evaluate_tokens(token.value, depth=depth + 1)
            self.log(tokens=[AssignmentToken(variable, value, token.echo)],
                     depth=depth)
            self.variables[variable] = value
            return value if token.echo else ''

        if isinstance(token, LiteralToken):
            string = token.string
        elif isinstance(token, PatternToken):
            string = self.evaluate_tokens(token.tokens, depth=depth + 1)
        elif isinstance(token, RangeToken):
            choice = random.choice(token.range)
            if token.alpha:
                string = chr(choice)
            else:
                string = str(choice)
        elif isinstance(token, SymbolToken):
            symbol = self.evaluate_tokens(token.symbol, depth=depth + 1)
            rule = self.produce(symbol)
            string = self.evaluate_tokens(rule.tokens, depth=depth + 1)
        elif isinstance(token, VariableToken):
            variable = token.variable
            value = self.variables.get(variable)
            if value is None:
                raise MayhapError(f'Variable "{variable}" not found')
            string = value

        if token.modifiers:
            self.log(tokens=[LiteralToken(string, token.modifiers)],
                     depth=depth)
            for modifier in token.modifiers:
                if modifier == MOD_PLURAL:
                    string = get_plural(string)
                elif modifier == MOD_ARTICLE:
                    string = add_article(string)
                elif modifier == MOD_ORDINAL:
                    string = get_ordinal(string)
                elif modifier == MOD_CAPITALIZE:
                    string = string.capitalize()
                elif modifier == MOD_LOWER:
                    string = string.lower()
                elif modifier == MOD_UPPER:
                    string = string.upper()
                elif modifier == MOD_TITLE:
                    string = string.title()
                elif modifier == MOD_MUNDANE:
                    pass
                else:
                    raise MayhapError(f'Unknown modifier "{modifier}"')

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
        rule = Rule.parse(pattern)
        string = self.evaluate_tokens(rule.tokens)
        return string

    def handle_input(self, pattern):
        try:
            print(self.evaluate_input(pattern))
            return True
        except MayhapError as e:
            print_error(e, self.verbose)
            return False


def filter_completions(command, completions):
    return [completion for completion in completions if
            completion.startswith(command)]


class MayhapShell(Cmd):
    def __init__(self, generator):
        super().__init__()
        self.generator = generator
        self.prompt = '> '

    @property
    def symbols(self):
        return list(self.generator.grammar.keys())

    def precmd(self, line):
        if line and line != 'EOF':
            if line.startswith(COMMAND_PREFIX):
                line = line[len(COMMAND_PREFIX):]
            else:
                line = 'evaluate ' + line
        return line

    def completenames(self, text, *ignored):
        command_started = text.startswith(COMMAND_PREFIX)
        if command_started:
            command = text[len(COMMAND_PREFIX):]
        else:
            command = text
        commands = super().completenames(command)
        if not command_started:
            commands = [COMMAND_PREFIX + command for command in commands]
        completions = []
        if not text or command_started:
            completions += commands
        if not text or not command_started:
            completions += self.symbols
        completions = filter_completions(command, completions)
        return completions

    # pylint: disable=arguments-differ, unused-argument
    def completedefault(self, text, line, *args):
        if ' ' in line:
            return filter_completions(text, self.symbols)
        return self.completenames(line, line, args)

    def do_evaluate(self, arg):
        '''
        Evaluate the given argument as a pattern. If the argument exactly
        matches a symbol, it is expanded. Called automatically if no command is
        specified.
        '''
        self.generator.handle_input(arg)

    def do_grammar(self, arg):
        '''
        Display the parsed form of the loaded grammar.
        '''
        print(grammar_to_string(self.generator.grammar))

    def do_list(self, arg):
        '''
        List the symbols in the current grammar if no argument is given. List
        the expansions of the given symbol if an argument is given.
        '''
        if not arg:
            print('\n'.join(self.symbols))
        else:
            symbol = arg
            rules = self.generator.grammar[symbol]
            print(join_as_strings(rules, delimiter='\n'))

    def do_add(self, arg):
        '''
        Add a new symbol and/or rule to the grammar.
        '''
        if not arg:
            print('Usage: add [symbol] [rule]')
            return
        terms = arg.split(' ')
        symbol = terms[0]
        if symbol in self.generator.grammar:
            if len(terms) == 1:
                print(f'Symbol "{symbol}" already exists')
                return
        else:
            self.generator.grammar[symbol] = set()
        if len(terms) > 1:
            rule_string = arg[len(symbol):].strip()
            rule = Rule.parse(rule_string)
            self.generator.grammar[symbol].add(rule)

    def do_remove(self, arg):
        '''
        Remove a symbol and/or rule from the grammar.
        '''
        if not arg:
            print('Usage: remove [symbol] [rule]')
            return

        terms = arg.split(' ')
        if len(terms) > 2:
            print('Usage: remove [symbol] [rule]')
            return

        symbol = terms[0]
        if symbol not in self.generator.grammar:
            print(f'Symbol "{symbol}" does not exist')
            return

        if len(terms) == 1:
            self.generator.grammar.remove(symbol)
            return

        rule_string = arg[len(symbol):].strip()
        rules = self.generator.grammar[symbol]
        for rule in rules:
            if str(rule) == rule_string:
                rules.remove(rule)
                return
        print(f'Symbol "{symbol}" has no rule "{rule_string}"')

    def do_import(self, arg):
        '''
        Import another grammar file.
        NOTE: The path you give must be relative to the grammar file you
        opened.
        '''
        if not arg:
            print('Usage: import [path to grammar file]')
            return
        try:
            imported_grammar = import_grammar(arg)
            self.generator.grammar |= imported_grammar
            self.generator.unused |= deepcopy(imported_grammar)
        except MayhapError as e:
            print_error(e, self.generator.verbose)

    # pylint: disable=no-self-use
    def do_exit(self, arg):
        '''
        Exit the shell.
        '''
        return True

    # pylint: disable=no-self-use
    def do_EOF(self, arg):
        # TODO don't show EOF as a command option
        print()
        return True


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
    interactive_group = parser.add_mutually_exclusive_group()
    interactive_group.add_argument(
            '-i', '--interactive',
            action='store_true',
            help='run as an interactive shell (default if reading from a TTY)')
    interactive_group.add_argument(
            '-b', '--batch',
            action='store_true',
            help='use non-interactive batch processing mode (default if '
                 'reading from a pipe)')
    interactive_group.add_argument(
            '-t', '--test',
            action='store_true',
            help='test the grammar by evaluating every rule and printing any '
                 'errors')
    parser.add_argument(
            '-v', '--verbose',
            action='store_true',
            help='explain what is being done; extra messages are written to '
                 'stderr, so stdout is still clean')
    args = parser.parse_args()

    # Change working directory to directory containing the given grammar
    # This allows for import paths relative to the given grammar
    chdir(dirname(args.grammar.name))

    try:
        grammar = parse_grammar(args.grammar)
    except MayhapError as e:
        print_error(e, args.verbose)
        return 1

    if args.verbose:
        print(grammar_to_string(grammar), file=stderr)

    generator = Generator(grammar, args.verbose)

    if args.test:
        failures = 0
        for symbol, rules in grammar.items():
            for rule in rules:
                try:
                    generator.evaluate_tokens(rule.tokens)
                except MayhapError as e:
                    print(symbol)
                    print('\t' + join_as_strings(rule.tokens))
                    print_error(e, generator.verbose)
                    print()
                    failures += 1
        if failures > 0:
            print(f'FAILED (failures={failures})')
        else:
            print('OK')
        return failures

    # If a pattern was given, generate it and exit
    if args.pattern:
        return 0 if generator.handle_input(args.pattern) else 1

    if args.interactive:
        use_shell = True
    elif args.batch:
        use_shell = False
    else:
        use_shell = isatty(stdin.fileno())

    # Otherwise, read standard input
    try:
        if use_shell:
            MayhapShell(generator).cmdloop()
        else:
            for line in stdin:
                # Strip trailing newline
                line = line[:-1]
                success = generator.handle_input(line)
                if not success:
                    return 1
    except KeyboardInterrupt:
        # Quietly handle SIGINT, like cat does
        print()
        return 1
    except EOFError:
        # Quietly handle EOF in interactive mode
        print()
        return 0

    return 0


if __name__ == '__main__':
    # Propagate return code
    sys.exit(main())
