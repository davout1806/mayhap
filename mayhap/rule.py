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

import random

from .common import join_as_strings


# The default weight for rules with no explicit weight
DEFAULT_WEIGHT = 1.0


class Rule:
    def __init__(self, tokens, weight=DEFAULT_WEIGHT):
        self.tokens = tuple(tokens)
        self.weight = weight

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


def choose_rule(rules):
    '''
    Choose a production from the given weighted list of rules.
    '''
    rules_tuple = tuple(rules)
    weights = [rule.weight for rule in rules_tuple]
    rule = random.choices(rules_tuple, weights)[0]
    return rule
