#!/usr/bin/env python3
import unittest

from mayhap import (AssignmentToken,
                    ChoiceToken,
                    LiteralToken,
                    PatternToken,
                    RangeToken,
                    Rule,
                    SymbolToken,
                    VariableToken)


class TestRule(unittest.TestCase):
    def test_string(self):
        '''
        Parsing a rule with a top-level string literal: string
        '''
        expected = Rule(['string'])
        actual = Rule.parse('string')
        self.assertEqual(expected, actual)

    def test_literal(self):
        '''
        Parsing a rule with a literal token: ['literal']
        '''
        expected = Rule([LiteralToken('literal')])
        actual = Rule.parse("['literal']")
        self.assertEqual(expected, actual)

    def test_pattern(self):
        '''
        Parsing a rule with a pattern token: ["pattern"]
        '''
        expected = Rule([PatternToken(['pattern'])])
        actual = Rule.parse('["pattern"]')
        self.assertEqual(expected, actual)

    def test_range_num(self):
        '''
        Parsing a rule with a numeric range: [1-5]
        '''
        expected = Rule([RangeToken(range(1, 5 + 1), alpha=False)])
        actual = Rule.parse('[1-5]')
        self.assertEqual(expected, actual)

    def test_range_alpha(self):
        '''
        Parsing a rule with an alphabetic range: [q-v]
        '''
        expected = Rule([RangeToken(range(ord('q'), ord('v') + 1),
                                    alpha=True)])
        actual = Rule.parse('[q-v]')
        self.assertEqual(expected, actual)

    def test_range_num_modded(self):
        '''
        Parsing a rule with a numeric range and a modifier: [1-5.ordinal]
        '''
        expected = Rule([RangeToken(range(1, 5 + 1),
                         alpha=False,
                         modifiers=['ordinal'])])
        actual = Rule.parse('[1-5.ordinal]')
        self.assertEqual(expected, actual)

    def test_symbol(self):
        '''
        Parsing a rule with a symbol: [symbol]
        '''
        expected = Rule([SymbolToken('symbol')])
        actual = Rule.parse('[symbol]')
        self.assertEqual(expected, actual)

    def test_symbol_modded(self):
        '''
        Parsing a rule with a symbol and a modifier: [symbol.mundane]
        '''
        expected = Rule([SymbolToken('symbol', modifiers=['mundane'])])
        actual = Rule.parse('[symbol.mundane]')
        self.assertEqual(expected, actual)

    def test_variable(self):
        '''
        Parsing a rule with a variable: [$variable]
        '''
        expected = Rule([VariableToken('variable')])
        actual = Rule.parse('[$variable]')
        self.assertEqual(expected, actual)

    def test_assignment(self):
        '''
        Parsing a rule with a variable assignment: [variable=symbol]
        '''
        expected = Rule([AssignmentToken('variable',
                                         [SymbolToken('symbol')],
                                         echo=True)])
        actual = Rule.parse("[variable=symbol]")
        self.assertEqual(expected, actual)

    def test_choices(self):
        '''
        Parsing a rule with choices: [choice1|choice2]
        '''
        expected = Rule([ChoiceToken([Rule(['choice1']), Rule(['choice2'])])])
        actual = Rule.parse("[choice1|choice2]")
        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
