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

from os.path import isfile
import re

from pyparsing import (Combine,
                       Forward,
                       Literal,
                       OneOrMore,
                       Optional,
                       ParseException,
                       StringEnd,
                       StringStart,
                       Suppress,
                       QuotedString,
                       Word,
                       ZeroOrMore,
                       alphas,
                       printables,
                       pyparsing_common)

from .common import MayhapError, MayhapGrammarError
from .rule import Rule
from .tokens import (LiteralToken,
                     PatternToken,
                     RangeToken,
                     SymbolToken,
                     VariableToken,
                     AssignmentToken,
                     ChoiceToken,
                     WeightToken)


def word_excluding(exclude_chars):
    return Word(printables + ' ',
                exclude_chars=exclude_chars).leave_whitespace()


def parse_literal_action(toks):
    return LiteralToken(toks[0])


def parse_pattern_action(toks):
    return PatternToken(tuple(toks))


def parse_range_num_action(toks):
    bound1 = toks[0]
    bound2 = toks[1]
    start = min(bound1, bound2)
    stop = max(bound1, bound2) + 1
    return RangeToken(range(start, stop), alpha=False)


def parse_range_alpha_action(toks):
    if toks[0].isupper() != toks[1].isupper():
        raise MayhapError(f'Range bounds ({toks[0]} and {toks[1]}) must have '
                          'the same case')
    bound1 = ord(toks[0])
    bound2 = ord(toks[1])
    start = min(bound1, bound2)
    stop = max(bound1, bound2) + 1
    return RangeToken(range(start, stop), alpha=True)


def parse_symbol_action(toks):
    return SymbolToken(toks[0])


def parse_variable_action(toks):
    return VariableToken(toks[0])


def parse_assignment_echo_action(toks):
    return AssignmentToken(toks[0], tuple(toks[1:]), echo=True)


def parse_assignment_silent_action(toks):
    return AssignmentToken(toks[0], tuple(toks[1:]), echo=False)


def parse_choices_action(toks):
    rules = [(rule if rule else Rule([])) for rule in toks]
    return ChoiceToken(tuple(rules))


def parse_modifiers_action(toks):
    toks[0].modifiers = tuple(toks[1:])
    return toks[0]


def parse_weight_action(toks):
    return WeightToken(toks[0])


def parse_rule_action(toks):
    if len(toks) > 0 and isinstance(toks[-1], WeightToken):
        if len(toks) > 1:
            tokens = toks[:-2] + [toks[-2].rstrip()]
        else:
            tokens = []
        return Rule(tokens, toks[-1].weight)
    return Rule(toks)


# Parser expressions
E_WEIGHT = Suppress('^') + pyparsing_common.fnumber.copy()
E_WEIGHT.add_parse_action(parse_weight_action)

E_SPECIAL = Forward()

E_BLOCK = Suppress('[') + E_SPECIAL + Suppress(']')

E_UNQUOTED_TEXT = Combine(OneOrMore(word_excluding('"[]'))).leave_whitespace()
E_UNQUOTED_TOKEN = Forward()

E_LITERAL = QuotedString("'", esc_char='\\', multiline=True)
E_LITERAL.add_parse_action(parse_literal_action)

E_PATTERN = Suppress('"') + OneOrMore(E_UNQUOTED_TOKEN) + Suppress('"')
E_PATTERN.add_parse_action(parse_pattern_action)

E_RANGE_NUM = (pyparsing_common.signed_integer()
               + Suppress('-')
               + pyparsing_common.signed_integer())
E_RANGE_NUM.add_parse_action(parse_range_num_action)

E_RANGE_ALPHA = Word(alphas, exact=1) + Suppress('-') + Word(alphas, exact=1)
E_RANGE_ALPHA.add_parse_action(parse_range_alpha_action)

E_RANGE = E_RANGE_NUM | E_RANGE_ALPHA

E_SYMBOL = pyparsing_common.identifier.copy()
E_SYMBOL.add_parse_action(parse_symbol_action)

E_VARIABLE = pyparsing_common.identifier.copy()
E_VARIABLE_ACCESS = Suppress('$') + E_VARIABLE
E_VARIABLE_ACCESS.add_parse_action(parse_variable_action)

E_ASSIGNMENT_ECHO = E_VARIABLE + Literal('=').suppress() + E_SPECIAL
E_ASSIGNMENT_ECHO.add_parse_action(parse_assignment_echo_action)
E_ASSIGNMENT_SILENT = E_VARIABLE + Literal('~').suppress() + E_SPECIAL
E_ASSIGNMENT_SILENT.add_parse_action(parse_assignment_silent_action)
E_ASSIGNMENT = E_ASSIGNMENT_ECHO | E_ASSIGNMENT_SILENT

E_RULE = Forward()
E_CHOICES = (Optional(E_RULE, default=None).leave_whitespace()
             + OneOrMore(Suppress('|')
                         + Optional(E_RULE, default=None).leave_whitespace()))
E_CHOICES.add_parse_action(parse_choices_action)

E_MODIFIER = Suppress('.') + pyparsing_common.identifier.copy()
E_MODDED = ((E_LITERAL | E_PATTERN | E_RANGE | E_SYMBOL | E_VARIABLE_ACCESS)
            + ZeroOrMore(E_MODIFIER))
E_MODDED.add_parse_action(parse_modifiers_action)

E_SPECIAL <<= E_ASSIGNMENT | E_CHOICES | E_MODDED

E_UNQUOTED_TOKEN <<= (E_UNQUOTED_TEXT | E_BLOCK).leave_whitespace()

E_TEXT = Combine(OneOrMore(word_excluding('|^[]'))).leave_whitespace()
E_TOKEN = (E_TEXT | E_BLOCK).leave_whitespace()

E_RULE <<= ZeroOrMore(E_TOKEN) + Optional(E_WEIGHT)
E_RULE.add_parse_action(parse_rule_action)

E_RULE_LINE = StringStart() + E_RULE + StringEnd()


# Matches the name of a generator to import when parsing a grammar
# e.g. @generator_name
# e.g. @/home/username/generator_name.mh
RE_IMPORT = re.compile(r'@(.+)')

# Matches comments (lines starting with a hash)
# e.g. \t# hello world
RE_COMMENT = re.compile(r'(^|[^\\])(#.*)')

# Matches a backslash-escaped character
# e.g. \[, \n, \\
RE_ESCAPE = re.compile(r'\\(.)')

# All characters special to Mayhap that can be escaped with a backslash
SPECIAL_CHARS = set('"^[]|')


def parse_rule(string):
    '''
    Parses an production rule into a weight and a production string.
    '''
    def escape_repl(match):
        if match[1] == "'":
            return "\\'"
        if match[1] in SPECIAL_CHARS:
            unescaped = match[1]
        else:
            unescaped = (match[0].encode('raw_unicode_escape')
                                 .decode('unicode_escape'))
        return f"['{unescaped}']"

    string = RE_ESCAPE.sub(escape_repl, string)
    try:
        return E_RULE_LINE.parse_with_tabs().parse_string(string)[0]
    except ParseException as e:
        raise MayhapError(f'Error parsing rule: {e}') from e


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
                    rule = parse_rule(stripped)
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

                if len(E_SYMBOL.search_string(current_symbol)) != 1:
                    raise MayhapGrammarError('Invalid symbol name: '
                                             f'{current_symbol}',
                                             i + 1, line)

                grammar[current_symbol] = set()

    if current_symbol and not grammar[current_symbol]:
        raise MayhapGrammarError(f'Symbol "{current_symbol}" closed with no '
                                 'production rules', len(lines), lines[-1])

    return grammar


def grammar_to_string(grammar):
    string = ''
    for symbol, rules in grammar.items():
        string += f'{symbol}\n'
        for rule in rules:
            string += f'\t{rule}\n'
    return string
