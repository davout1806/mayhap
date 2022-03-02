# TODO

## Refactoring

- Use pyparsing to parse grammars as well as rules
- Reorganize project to follow Python package structure

## Grammar Features

- Ranges:
	- Decimal ranges: `[0.5-2.5]` (output uses the same digits of precision as the more precise number in the range)
	- Dice parsing: `[2d6+3]`
		- Regex: `(\d+)d(\d+)([+-](\d+)d(\d+))*([+-]\d+)?`
		- `dice` module
- Fractional weights(?): `^2/5.5`
- Repeated accesses: `[5 * 0-9]`
- Inflections:
	- Conditional pluralization: `[x=1-5] [item.s($x)]`
	- Present participle: `[verb.ing]`
		- `inflect.present_participle`
	- Pronouns:
		- `[$gender = m|f|n|x]`
		- `[$gender.they]`, `[$gender.them]`, etc.
		- Use `inflect.gender` and `inflect.singular_noun`
	- Tense: `[verb.ed]`, etc.
		- https://github.com/clips/pattern (currently lacking Python 3.7 support)
- Local variable scoping(?): `$_local`?
- Parameterized rules:
	- Symbol definition: `greet(name)`
	- Rule definition: `Hi, [$name]!`
	- Invocation: `[greet('Bob')]`
- Markov chains: `@markov symbolname`?
- Escape characters:
	- As a pre-processing pass, convert `\*` to `['*']` (where `*` is any escapable character)
	- This should work, because anywhere a block could legally be escaped is necessarily a place where a block could occur
	- Handle `\n` and `\t` as special cases
	- Handle `\\` by converting it to `\` (not putting it in a literal token)
	- Ideally, backslashes would be ignored in single quotes, but that would require more intelligent pre-processing
- Add syntax to reference symbols
	- Symbol reference: `[x = &symbol]`
	- Symbol dereference: `[$x]` (chooses a different production for symbol each time `x` is accessed)
- C-style format strings: `['%02d' % [0-60]]`
- Remove `a(n)` and `(s)` in favor of `.a` and `.s()` (when implemented)
- Query [corpora](https://github.com/aparrish/pycorpora) and other sources for common data
- Namespaces for imported grammars: `[animals::bird]`
	- Custom namespace: `@namespace mynamespace`?
	- Import with a custom namespace ("import as")
- Conditional logic: `[$a == '1' ? symbol1 : symbol2]`
- Math expressions
- Consider using braces to group rules by symbol rather than indentation
	- Slightly less nice to read/write
	- Renders leading whitespace insignificant (or literal?)

## Program Features

- Point to the character where an error happened (strip indentation)
- Warn when running out of unique symbols
- Flags
	- Control whether unused variables are preserved between queries (`persistent`, false by default)
	- Make symbols default to mundane
	- Force uniqueness (fail when running out of unique symbols)
	- Maximum recursion depth for recursive symbols
- Validation
	- Validate modifiers while parsing
	- Validate symbols after parsing
	- Validate variables after parsing
	- Warn about unused symbols
	- Warn about unused variables
- Basic optimizations
	- Replace unmodified literal tokens into strings and merge with neighbors
	- Unpack unmodified pattern tokens
	- Resolve deterministic literal modifiers while parsing
	- Resolve deterministic inflections after parsing
- Arguments
	- Enable/disable warnings
	- Enable/disable validation
	- Enable/disable optimizations
	- Just validate grammar and exit
	- Print standardized grammar (output of `print_grammar`)
- Shell commands
	- Save grammar to file: `/export path_to_grammar.mh`
	- Toggle generator flags: `/set verbose`/`/unset verbose` or `/set verbose true`
- Improve autocomplete and fix autocomplete for help
- Run file as shell script (use `Cmd` but disable prompt)

## Non-Functional

- Syntax documentation/tutorial
- Test suite
	- Escapes
		- Literal caret
		- Caret in literal token
		- Block in literal token
		- Escaped quotes in pattern token
		- Pattern token in pattern token
	- Importing
	- Regression tests (compile all samples and compare new compiles against saved versions)
	- Performance tests (generate large grammar and query files)
- Create a vim syntax file for Mayhap grammars
