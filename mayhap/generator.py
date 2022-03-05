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

from copy import deepcopy
import random
from sys import stderr

from .common import MayhapError, join_as_strings, print_error
from .modifiers import (MOD_MUNDANE,
                        apply_modifier,
                        resolve_indefinite_articles,
                        resolve_plurals)
from .parse import parse_rule
from .rule import choose_rule
from .tokens import (LiteralToken,
                     PatternToken,
                     RangeToken,
                     SymbolToken,
                     VariableToken,
                     AssignmentToken,
                     ChoiceToken)


class MayhapGenerator:
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

            rule = choose_rule(self.unused[symbol])
            self.unused[symbol].remove(rule)
            return rule

        rules = self.grammar[symbol]
        if rules is None:
            raise MayhapError(f'Symbol "{symbol}" not found')
        rule = choose_rule(rules)
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
            rule = choose_rule(token.rules)
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
            unique = MOD_MUNDANE not in token.modifiers
            rule = self.produce(symbol, unique)
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
                string = apply_modifier(string, modifier)

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
        rule = parse_rule(pattern)
        string = self.evaluate_tokens(rule.tokens)
        return string

    def handle_input(self, pattern):
        try:
            print(self.evaluate_input(pattern))
            return True
        except MayhapError as e:
            print_error(e, self.verbose)
            return False
