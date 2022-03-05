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

from cmd import Cmd
from copy import deepcopy

from .common import MayhapError, join_as_strings, print_error
from .parse import grammar_to_string, import_grammar, parse_rule


# The string that prefixes commands in interactive mode
# Non-command inputs are interpreted as patterns or symbols
COMMAND_PREFIX = '/'


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
            rule = parse_rule(rule_string)
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
