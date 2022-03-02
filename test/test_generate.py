from unittest import TestCase

from mayhap import (AssignmentToken,
                    ChoiceToken,
                    Generator,
                    LiteralToken,
                    MayhapError,
                    PatternToken,
                    RangeToken,
                    Rule,
                    SymbolToken,
                    VariableToken)


class TestGenerate(TestCase):
    def test_string(self):
        '''
        Evaluating a string literal: string
        '''
        generator = Generator({})
        expected = 'string'
        actual = generator.evaluate_token('string')
        self.assertEqual(expected, actual)

    def test_literal(self):
        '''
        Evaluating a literal token: ['literal']
        '''
        generator = Generator({})
        expected = 'literal'
        actual = generator.evaluate_token(LiteralToken('literal'))
        self.assertEqual(expected, actual)

    def test_pattern(self):
        '''
        Evaluating a pattern token: ["pattern"]
        '''
        generator = Generator({})
        expected = 'pattern'
        actual = generator.evaluate_token(PatternToken(['pattern']))
        self.assertEqual(expected, actual)

    def test_pattern_nested(self):
        '''
        Evaluating a literal nested in a pattern: ["['literal']"]
        '''
        generator = Generator({})
        expected = 'literal'
        actual = generator.evaluate_token(PatternToken([
            LiteralToken('literal')
        ]))
        self.assertEqual(expected, actual)

    def test_range_num(self):
        '''
        Evaluating a numeric range: [1-5]
        '''
        generator = Generator({})
        actual = generator.evaluate_token(RangeToken(range(1, 5 + 1),
                                                     alpha=False))
        self.assertTrue(int(actual) in range(1, 5 + 1))

    def test_range_alpha(self):
        '''
        Evaluating an alphabetic range: [a-c]
        '''
        generator = Generator({})
        actual = generator.evaluate_token(RangeToken(
            range(ord('a'), ord('c') + 1),
            alpha=True))
        self.assertTrue(actual in tuple('abc'))

    def test_symbol(self):
        '''
        Evaluating a symbol token: [symbol]
        '''
        generator = Generator({
            'symbol': set([
                Rule(['rule']),
            ]),
        })
        expected = 'rule'
        actual = generator.evaluate_token(SymbolToken('symbol'))
        self.assertEqual(expected, actual)

    def test_variable(self):
        '''
        Evaluating a variable: [$variable]
        '''
        generator = Generator({})
        generator.variables = {'variable': 'value'}
        expected = 'value'
        actual = generator.evaluate_token(VariableToken('variable'))
        self.assertEqual(expected, actual)

    def test_assignment_echoed(self):
        '''
        Evaluating an echoed variable assignment: [variable='value']
        '''
        generator = Generator({})
        expected = 'value'
        actual = generator.evaluate_token(AssignmentToken(
            'variable',
            [LiteralToken('value')],
            echo=True))
        self.assertEqual(expected, actual)

    def test_assignment_silent(self):
        '''
        Evaluating a silent variable assignment: [variable~'value']
        '''
        generator = Generator({})
        expected = ''
        actual = generator.evaluate_token(AssignmentToken(
            'variable',
            [LiteralToken('value')],
            echo=False))
        self.assertEqual(expected, actual)

    def test_reassignment(self):
        '''
        Evaluating a variable before and after assignment:
        [$variable][variable~'value2'][$variable]
        '''
        generator = Generator({})
        generator.variables = {'variable': 'value1'}
        expected = 'value1value2'
        actual = generator.evaluate_tokens([
            VariableToken('variable'),
            AssignmentToken('variable',
                            [LiteralToken('value2')],
                            echo=False),
            VariableToken('variable'),
        ])
        self.assertEqual(expected, actual)

    def test_choices(self):
        '''
        Evaluating choices: [choice1|choice2]
        '''
        generator = Generator({})
        actual = generator.evaluate_token(ChoiceToken([Rule(['choice1']),
                                                       Rule(['choice2'])]))
        self.assertTrue(actual in ('choice1', 'choice2'))

    def test_weight(self):
        '''
        Evaluating a symbol with only one possible rule.
        '''
        generator = Generator({
            'symbol': set([
                Rule(['possible'], weight=1.0),
                Rule(['impossible'], weight=0.0),
            ]),
        })
        expected = 'possible'
        actual = generator.evaluate_input('symbol')
        self.assertEqual(expected, actual)

    def test_pattern_string(self):
        '''
        Evaluating a literal string pattern: string
        '''
        generator = Generator({})
        expected = 'string'
        actual = generator.evaluate_input('string')
        self.assertEqual(expected, actual)

    def test_undefined_symbol(self):
        '''
        Evaluating a symbol that does not exist: [symbol]
        '''
        generator = Generator({})
        with self.assertRaises(MayhapError):
            generator.evaluate_token(SymbolToken('symbol'))

    def test_undefined_variable(self):
        '''
        Evaluating a variable before it is defined: [$variable]
        '''
        generator = Generator({})
        with self.assertRaises(MayhapError):
            generator.evaluate_token(VariableToken('variable'))
