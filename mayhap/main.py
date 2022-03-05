from argparse import ArgumentParser, FileType
from os import chdir, isatty
from os.path import dirname
from sys import stderr, stdin

from .common import MayhapError, join_as_strings, print_error
from .generator import MayhapGenerator
from .parse import grammar_to_string, parse_grammar
from .shell import MayhapShell


def main():
    '''
    Parse arguments and handle input and output.
    '''
    parser = ArgumentParser(prog='mayhap',
                            description='A grammar-based random text '
                                        'generator, inspired by Perchance')
    parser.add_argument(
            'grammar',
            type=FileType('r'),
            help='file that defines the grammar to generate from')
    parser.add_argument(
            'pattern',
            nargs='?',
            help='the pattern to generate from the grammar; if this argument '
                 'is not provided, read from standard input instead')
    interactive_group = parser.add_mutually_exclusive_group()
    interactive_group.add_argument(
            '-i', '--interactive',
            action='store_true',
            help='run as an interactive shell (default if reading from a TTY)')
    interactive_group.add_argument(
            '-b', '--batch',
            action='store_true',
            help='use non-interactive batch processing mode (default if '
                 'reading from a pipe)')
    interactive_group.add_argument(
            '-t', '--test',
            action='store_true',
            help='test the grammar by evaluating every rule and printing any '
                 'errors')
    parser.add_argument(
            '-v', '--verbose',
            action='store_true',
            help='explain what is being done; extra messages are written to '
                 'stderr, so stdout is still clean')
    args = parser.parse_args()

    # Change working directory to directory containing the given grammar
    # This allows for import paths relative to the given grammar
    chdir(dirname(args.grammar.name))

    try:
        grammar = parse_grammar(args.grammar)
    except MayhapError as e:
        print_error(e, args.verbose)
        return 1

    if args.verbose:
        print(grammar_to_string(grammar), file=stderr)

    generator = MayhapGenerator(grammar, args.verbose)

    if args.test:
        failures = 0
        for symbol, rules in grammar.items():
            for rule in rules:
                try:
                    generator.evaluate_tokens(rule.tokens)
                except MayhapError as e:
                    print(symbol)
                    print('\t' + join_as_strings(rule.tokens))
                    print_error(e, generator.verbose)
                    print()
                    failures += 1
        if failures > 0:
            print(f'FAILED (failures={failures})')
        else:
            print('OK')
        return failures

    # If a pattern was given, generate it and exit
    if args.pattern:
        return 0 if generator.handle_input(args.pattern) else 1

    if args.interactive:
        use_shell = True
    elif args.batch:
        use_shell = False
    else:
        use_shell = isatty(stdin.fileno())

    # Otherwise, read standard input
    try:
        if use_shell:
            MayhapShell(generator).cmdloop()
        else:
            for line in stdin:
                # Strip trailing newline
                line = line[:-1]
                success = generator.handle_input(line)
                if not success:
                    return 1
    except KeyboardInterrupt:
        # Quietly handle SIGINT, like cat does
        print()
        return 1
    except EOFError:
        # Quietly handle EOF in interactive mode
        print()
        return 0

    return 0
