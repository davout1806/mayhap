from unittest import TestCase

from mayhap.common import MayhapError
from mayhap.parse import parse_rule
from mayhap.rule import Rule
from mayhap.tokens import (AssignmentToken,
                           ChoiceToken,
                           RangeToken,
                           SymbolToken,
                           VariableToken)


class TestRule(TestCase):
    def test_string(self):
        '''
        Parsing a rule with a top-level string literal: string
        '''
        expected = Rule(['string'])
        actual = parse_rule('string')
        self.assertEqual(expected, actual)

    def test_single_quoted_string(self):
        '''
        Parsing a rule with a top-level string literal with single quotes:
        'string'
        '''
        expected = Rule(["'string'"])
        actual = parse_rule("'string'")
        self.assertEqual(expected, actual)

    def test_double_quoted_string(self):
        '''
        Parsing a rule with a top-level string literal with double quotes:
        'string'
        '''
        expected = Rule(['"string"'])
        actual = parse_rule('"string"')
        self.assertEqual(expected, actual)

    def test_escaped_block(self):
        '''
        Parsing a rule with a backspace-escaped block: \\[not_a_block\\]
        '''
        expected = Rule(['[not_a_block]'])
        actual = parse_rule('\\[not_a_block\\]')
        self.assertEqual(expected, actual)

    def test_escaped_weight(self):
        '''
        Parsing a rule with a backslash-escaped weight: not a weight \\^2
        '''
        expected = Rule(['not a weight ^2'])
        actual = parse_rule('not a weight \\^2')
        self.assertEqual(expected, actual)

    def test_escape_sequences(self):
        '''
        Parsing a rule with backslash-escaped escape sequences: \\t\\n
        '''
        expected = Rule(['\t\n'])
        actual = parse_rule('\\t\\n')
        self.assertEqual(expected, actual)

    def test_weight(self):
        '''
        Parsing a rule with a weight: string^0.5
        '''
        expected = Rule(['string'], weight=0.5)
        actual = parse_rule('string^0.5')
        self.assertEqual(expected, actual)

    def test_weight_whitespace(self):
        '''
        Parsing a rule with a weight separated with whitespace: string ^0.5
        '''
        expected = Rule(['string'], weight=0.5)
        actual = parse_rule('string ^0.5')
        self.assertEqual(expected, actual)

    def test_negative_weight(self):
        '''
        Parsing a rule with a negative weight: string ^-5
        '''
        with self.assertRaises(MayhapError):
            parse_rule('string ^-5')

    def test_unclosed_block(self):
        '''
        Parsing a rule with an unclosed block: string [
        '''
        with self.assertRaises(MayhapError):
            parse_rule('string [')

    def test_closed_block(self):
        '''
        Parsing a rule with a prematurely closed block: string ]
        '''
        with self.assertRaises(MayhapError):
            parse_rule('string ]')

    def test_empty_block(self):
        '''
        Parsing a rule with an empty block: []
        '''
        with self.assertRaises(MayhapError):
            parse_rule('[]')

    def test_literal(self):
        '''
        Parsing a rule with a literal token: ['literal']
        '''
        expected = Rule(['literal'])
        actual = parse_rule("['literal']")
        self.assertEqual(expected, actual)

    def test_literal_modded(self):
        '''
        Parsing a rule with a literal token and a modifier: ['literal'.s]
        '''
        expected = Rule(['literals'])
        actual = parse_rule("['literal'.s]")
        self.assertEqual(expected, actual)

    def test_literal_escaped_quote(self):
        '''
        Parsing a rule with a literal token with an escaped single quote:
        ['literal\\'s']
        '''
        expected = Rule(["literal's"])
        actual = parse_rule("['literal\\'s']")
        self.assertEqual(expected, actual)

    def test_pattern(self):
        '''
        Parsing a rule with a pattern token: ["pattern"]
        '''
        expected = Rule(['pattern'])
        actual = parse_rule('["pattern"]')
        self.assertEqual(expected, actual)

    def test_pattern_modded(self):
        '''
        Parsing a rule with a pattern token and a modifier: ["pattern".upper]
        '''
        expected = Rule(['PATTERN'])
        actual = parse_rule('["pattern".upper]')
        self.assertEqual(expected, actual)

    def test_pattern_single_quote(self):
        '''
        Parsing a rule with a pattern token with a single quote:
        ["pattern's"]
        '''
        expected = Rule(["pattern's"])
        actual = parse_rule('["pattern\'s"]')
        self.assertEqual(expected, actual)

    def test_pattern_escaped_quote(self):
        '''
        Parsing a rule with a pattern token with an escaped double quote:
        ["pattern\\"s"]
        '''
        expected = Rule(['pattern"s'])
        actual = parse_rule('["pattern\\"s"]')
        self.assertEqual(expected, actual)

    def test_pattern_nested_literal(self):
        '''
        Parsing a rule with a literal nested in a pattern: ["['literal']"]
        '''
        expected = Rule(['literal'])
        actual = parse_rule('["[\'literal\']"]')
        self.assertEqual(expected, actual)

    def test_pattern_nested_pattern(self):
        '''
        Parsing a rule with a pattern nested in a pattern: ["["pattern"]"]
        '''
        expected = Rule(['pattern'])
        actual = parse_rule('["["pattern"]"]')
        self.assertEqual(expected, actual)

    def test_range_num(self):
        '''
        Parsing a rule with a numeric range: [1-5]
        '''
        expected = Rule([RangeToken(range(1, 5 + 1), alpha=False)])
        actual = parse_rule('[1-5]')
        self.assertEqual(expected, actual)

    def test_range_alpha_lower(self):
        '''
        Parsing a rule with a lowercase alphabetic range: [q-v]
        '''
        expected = Rule([RangeToken(range(ord('q'), ord('v') + 1),
                                    alpha=True)])
        actual = parse_rule('[q-v]')
        self.assertEqual(expected, actual)

    def test_range_alpha_upper(self):
        '''
        Parsing a rule with an uppercase alphabetic range: [E-M]
        '''
        expected = Rule([RangeToken(range(ord('E'), ord('M') + 1),
                                    alpha=True)])
        actual = parse_rule('[E-M]')
        self.assertEqual(expected, actual)

    def test_range_whitespace(self):
        '''
        Parsing a rule with a numeric range with whitespace: [1 - 5]
        '''
        expected = Rule([RangeToken(range(1, 5 + 1), alpha=False)])
        actual = parse_rule('[1 - 5]')
        self.assertEqual(expected, actual)

    def test_range_modded(self):
        '''
        Parsing a rule with a numeric range and a modifier: [1-5.th]
        '''
        expected = Rule([RangeToken(range(1, 5 + 1),
                         alpha=False,
                         modifiers=['th'])])
        actual = parse_rule('[1-5.th]')
        self.assertEqual(expected, actual)

    def test_range_mixed_alpha(self):
        '''
        Parsing a rule with a mixed alphabetic/numeric range: [1-a]
        '''
        with self.assertRaises(MayhapError):
            parse_rule('[1-a]')

    def test_range_mixed_case(self):
        '''
        Parsing a rule with an alphabetic range with mixed cases: [a-B]
        '''
        with self.assertRaises(MayhapError):
            parse_rule('[a-B]')

    def test_symbol(self):
        '''
        Parsing a rule with a symbol: [symbol]
        '''
        expected = Rule([SymbolToken('symbol')])
        actual = parse_rule('[symbol]')
        self.assertEqual(expected, actual)

    def test_symbol_whitespace(self):
        '''
        Parsing a rule with a symbol with whitespace: [ symbol ]
        '''
        expected = Rule([SymbolToken('symbol')])
        actual = parse_rule('[ symbol ]')
        self.assertEqual(expected, actual)

    def test_symbol_modded(self):
        '''
        Parsing a rule with a symbol and a modifier: [symbol.mundane]
        '''
        expected = Rule([SymbolToken('symbol', modifiers=['mundane'])])
        actual = parse_rule('[symbol.mundane]')
        self.assertEqual(expected, actual)

    def test_bad_symbol(self):
        '''
        Parsing a rule with an invalid symbol name: [symbol with spaces]
        '''
        with self.assertRaises(MayhapError):
            parse_rule('[symbol with whitespace]')

    def test_symbol_eval(self):
        '''
        Parsing a rule with a dynamic symbol dereference: [[symbol]]
        '''
        with self.assertRaises(MayhapError):
            parse_rule('[[symbol]]')

    def test_variable(self):
        '''
        Parsing a rule with a variable: [$variable]
        '''
        expected = Rule([VariableToken('variable')])
        actual = parse_rule('[$variable]')
        self.assertEqual(expected, actual)

    def test_variable_modded(self):
        '''
        Parsing a rule with a variable and a modifier: [$variable.lower]
        '''
        expected = Rule([VariableToken('variable', modifiers=['lower'])])
        actual = parse_rule('[$variable.lower]')
        self.assertEqual(expected, actual)

    def test_bad_variable(self):
        '''
        Parsing a rule with an invalid variable name: [$variable with spaces]
        '''
        with self.assertRaises(MayhapError):
            parse_rule('[$variable with spaces]')

    def test_variable_eval(self):
        '''
        Parsing a rule with a dynamic variable dereference: [$[variable]]
        '''
        with self.assertRaises(MayhapError):
            parse_rule('[$[$variable]]')

    def test_assignment_echoed(self):
        '''
        Parsing a rule with an echoed variable assignment: [variable=symbol]
        '''
        expected = Rule([AssignmentToken('variable',
                                         [SymbolToken('symbol')],
                                         echo=True)])
        actual = parse_rule("[variable=symbol]")
        self.assertEqual(expected, actual)

    def test_assignment_silent(self):
        '''
        Parsing a rule with a silent variable assignment: [variable~symbol]
        '''
        expected = Rule([AssignmentToken('variable',
                                         [SymbolToken('symbol')],
                                         echo=False)])
        actual = parse_rule("[variable~symbol]")
        self.assertEqual(expected, actual)

    def test_assignment_whitespace(self):
        '''
        Parsing a rule with a variable assignment with whitespace:
        [variable = symbol]
        '''
        expected = Rule([AssignmentToken('variable',
                                         [SymbolToken('symbol')],
                                         echo=True)])
        actual = parse_rule("[variable = symbol]")
        self.assertEqual(expected, actual)

    def test_chained_assignment(self):
        '''
        Parsing a rule with a chained variable assignment: [x=y=z]
        '''
        expected = Rule([AssignmentToken('x',
                                         [AssignmentToken('y',
                                                          [SymbolToken('z')],
                                                          echo=True)],
                                         echo=True)])
        actual = parse_rule("[x=y=z]")
        self.assertEqual(expected, actual)

    def test_choices(self):
        '''
        Parsing a rule with choices: [choice1|choice2]
        '''
        expected = Rule([ChoiceToken([Rule(['choice1']),
                                      Rule(['choice2'])])])
        actual = parse_rule("[choice1|choice2]")
        self.assertEqual(expected, actual)

    def test_choices_whitespace(self):
        '''
        Parsing a rule with choices with whitespace: [ choice1 | choice2 ]
        '''
        expected = Rule([ChoiceToken([Rule([' choice1 ']),
                                      Rule([' choice2 '])])])
        actual = parse_rule("[ choice1 | choice2 ]")
        self.assertEqual(expected, actual)

    def test_choices_empty(self):
        '''
        Parsing a rule with an empty choice: [choice|]
        '''
        expected = Rule([ChoiceToken([Rule(['choice']),
                                      Rule([])])])
        actual = parse_rule("[choice|]")
        self.assertEqual(expected, actual)

    def test_assignment_choices(self):
        '''
        Parsing a rule with a variable assignment to choices:
        [variable=choice1|choice2]
        '''
        expected = Rule([AssignmentToken('variable',
                                         [ChoiceToken([Rule(['choice1']),
                                                       Rule(['choice2'])])],
                                         echo=True)])
        actual = parse_rule("[variable=choice1|choice2]")
        self.assertEqual(expected, actual)

    def test_assignment_choices_whitespace(self):
        '''
        Parsing a rule with a variable assignment to choices with whitespace:
        [ variable = choice1 | choice2 ]
        '''
        expected = Rule([AssignmentToken('variable',
                                         [ChoiceToken([Rule([' choice1 ']),
                                                       Rule([' choice2 '])])],
                                         echo=True)])
        actual = parse_rule("[ variable = choice1 | choice2 ]")
        self.assertEqual(expected, actual)
