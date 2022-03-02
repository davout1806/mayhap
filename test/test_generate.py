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
                    VariableToken,
                    MOD_ARTICLE,
                    MOD_PLURAL,
                    MOD_ORDINAL,
                    MOD_CAPITALIZE,
                    MOD_LOWER,
                    MOD_UPPER,
                    MOD_TITLE)


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

    def test_mod_article(self):
        '''
        Evaluating a literal with the indefinite article modifier:
        ['article'.a]
        '''
        generator = Generator({})
        expected = 'an article'
        actual = generator.evaluate_token(LiteralToken(
            'article',
            modifiers=[MOD_ARTICLE]))
        self.assertEqual(expected, actual)

    def test_mod_plural(self):
        '''
        Evaluating a literal with the plural modifier: ['plural'.s]
        '''
        generator = Generator({})
        expected = 'plurals'
        actual = generator.evaluate_token(LiteralToken(
            'plural',
            modifiers=[MOD_PLURAL]))
        self.assertEqual(expected, actual)

    def test_mod_ordinal(self):
        '''
        Evaluating a literal with the ordinal modifier: ['1'.th]
        '''
        generator = Generator({})
        expected = '1st'
        actual = generator.evaluate_token(LiteralToken(
            '1',
            modifiers=[MOD_ORDINAL]))
        self.assertEqual(expected, actual)

    def test_mod_capitalize(self):
        '''
        Evaluating a literal with the capitalize modifier:
        ['capitalize'.capitalize]
        '''
        generator = Generator({})
        expected = 'Capitalize'
        actual = generator.evaluate_token(LiteralToken(
            'capitalize',
            modifiers=[MOD_CAPITALIZE]))
        self.assertEqual(expected, actual)

    def test_mod_lower(self):
        '''
        Evaluating a literal with the lower modifier: ['LOWER'.lower]
        '''
        generator = Generator({})
        expected = 'lower'
        actual = generator.evaluate_token(LiteralToken(
            'LOWER',
            modifiers=[MOD_LOWER]))
        self.assertEqual(expected, actual)

    def test_mod_upper(self):
        '''
        Evaluating a literal with the upper modifier: ['upper'.upper]
        '''
        generator = Generator({})
        expected = 'UPPER'
        actual = generator.evaluate_token(LiteralToken(
            'upper',
            modifiers=[MOD_UPPER]))
        self.assertEqual(expected, actual)

    def test_mod_title(self):
        '''
        Evaluating a literal with the title modifier: ['title case'.title]
        '''
        generator = Generator({})
        expected = 'Title Case'
        actual = generator.evaluate_token(LiteralToken(
            'title case',
            modifiers=[MOD_TITLE]))
        self.assertEqual(expected, actual)

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
