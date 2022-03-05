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

from .common import MayhapError, join_as_strings


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


class WeightToken:
    def __init__(self, weight):
        if weight < 0:
            raise MayhapError(f'Weight must be non-negative; was {weight}')
        self.weight = weight
