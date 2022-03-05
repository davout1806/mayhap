from unittest import TestCase

from mayhap.core import MayhapGrammarError, Rule, parse_grammar


class TestGrammar(TestCase):
    def test_one_rule(self):
        '''
        Parsing a grammar with one symbol and one rule.
        '''
        expected = {
            'symbol': set([
                Rule(['rule']),
            ]),
        }
        actual = parse_grammar([
            'symbol',
            '\trule',
        ])
        self.assertEqual(expected, actual)

    def test_multiple_rules(self):
        '''
        Parsing a grammar with one symbol and multiple rules.
        '''
        expected = {
            'symbol': set([
                Rule(['rule1']),
                Rule(['rule2']),
                Rule(['rule3']),
            ]),
        }
        actual = parse_grammar([
            'symbol',
            '\trule1',
            '\trule2',
            '\trule3',
        ])
        self.assertEqual(expected, actual)

    def test_multiple_symbols(self):
        '''
        Parsing a grammar with multiple symbols and rules.
        '''
        expected = {
            'symbol1': set([
                Rule(['rule1']),
            ]),
            'symbol2': set([
                Rule(['rule2']),
            ]),
        }
        actual = parse_grammar([
            'symbol1',
            '\trule1',
            'symbol2',
            '\trule2',
        ])
        self.assertEqual(expected, actual)

    def test_blank_lines(self):
        '''
        Parsing a grammar with multiple symbols and rules, with blank lines.
        '''
        expected = {
            'symbol1': set([
                Rule(['rule1']),
            ]),
            'symbol2': set([
                Rule(['rule2']),
            ]),
        }
        actual = parse_grammar([
            'symbol1',
            '\trule1',
            '',
            'symbol2',
            '',
            '\trule2',
        ])
        self.assertEqual(expected, actual)

    def test_standalone_comment(self):
        '''
        Parsing a grammar with a comment on its own line.
        '''
        expected = {
            'symbol': set([
                Rule(['rule']),
            ]),
        }
        actual = parse_grammar([
            '# comment',
            'symbol',
            '\trule',
        ])
        self.assertEqual(expected, actual)

    def test_inline_comment(self):
        '''
        Parsing a grammar with inline comments.
        '''
        expected = {
            'symbol': set([
                Rule(['rule']),
            ]),
        }
        actual = parse_grammar([
            'symbol # comment',
            '\trule # comment',
        ])
        self.assertEqual(expected, actual)

    def test_rule_before_symbol(self):
        '''
        Parsing a grammar with a rule given before its symbol.
        '''
        with self.assertRaises(MayhapGrammarError):
            parse_grammar([
                '\trule',
                'symbol',
            ])

    def test_symbol_without_rules(self):
        '''
        Parsing a grammar with a symbol but no rules.
        '''
        with self.assertRaises(MayhapGrammarError):
            parse_grammar([
                'symbol',
            ])

    def test_bad_symbol(self):
        '''
        Parsing a grammar with an illegal symbol name.
        '''
        with self.assertRaises(MayhapGrammarError):
            parse_grammar([
                'symbol with spaces',
                '\trule',
            ])
