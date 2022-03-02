# TODO

## Refactoring

- Rewrite using `pyparsing` instead of regex and custom methods
- Reorganize project to follow Python package structure

## Grammar Features

- Ranges:
	- Decimal ranges: `[0.5-2.5]` (output uses the same digits of precision as the more precise number in the range)
	- Dice parsing: `[2d6+3]`
		- Regex: `(\d+)d(\d+)([+-](\d+)d(\d+))*([+-]\d+)?`
		- `dice` module
- Fractional weights `^2/5.5`
- Repeated accesses: `[5 * 0-9]`
- Parameterized modifiers: `[x=1-5] [item.s($x)]`
- Inflections:
	- Conditional pluralization: `[x=1-5] [item.s($x)]`
	- Present participle: `[verb.ing]`
		- `inflect.present_participle`
	- Pronouns:
		- `[$gender = ['masculine'|'feminine'|'gender-neutral']]`
		- Option 1: `['they'.gender($gender)]`
		- Option 2: `[gender.they]`
		- Use `inflect.gender` and `inflect.singular_noun`
	- Tense: `[verb.ed]`, etc.
		- https://github.com/clips/pattern (currently lacking Python 3.7 support)
- Case:
	- Lower case: `[symbol]`
	- Title case: `[Symbol]`
	- Upper case: `[SYMBOL]`
	- Limit symbol and variable names to alphanumeric and underscores, starting with a letter
- Allow modifiers for patterns and literals
- Local variable scoping
- Parameterized rules:
	- Symbol definition: `greet(name)`
	- Rule definition: `Hi, [$name]!`
	- Invocation: `[greet('Bob')]`
- Markov chains: `@markov symbolname`?
- Escape characters:
	- Intentional leading/trailing whitespace: `\ my rule \ ^2`
		- Workaround: `[' my rule '] ^2`
	- Blocks: `\[not a block\]`
	- a: `a\(n\)`
	- s: `\(s\)`
	- Weights: `\^not a weight`
	- Standard escapes: `\n`, `\t`, `\\`

	  ```py
	  my_string.encode('raw_unicode_escape').decode('unicode_escape')`
	  ```
- Add syntax to reference symbols?
	- Symbol reference: `[x = &symbol]`
	- Symbol dereference: `[$x]` (chooses a different production for symbol each time `x` is accessed)
	- Former workaround: `[x ~ 'symbol'][[$x]]`
- C-style format string support: `['%02d' % [0-60]]`
- Consider removing `a(n)` and `(s)` in favor of `.a` and `.s()` (when implemented)
- Query [corpora](https://github.com/aparrish/pycorpora) and other sources for common data
- Namespaces for imported grammars: `[animals:bird]`
	- Custom namespace: `@namespace mynamespace`?
	- Import with a custom namespace ("import as")

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
	- Generate all rules (for testing)
	- Print standardized grammar (output of `print_grammar`)
- Shell commands
	- Save grammar to file: `/export path_to_grammar.mh`
	- Toggle generator flags: `/set verbose`/`/unset verbose` or `/set verbose true`
- Improve autocomplete and fix autocomplete for help
- Run file as shell script (use `Cmd` but disable prompt)

## Non-Functional

- Syntax documentation/tutorial
- Test suite
	- Test modifiers
	- Test inflections
	- Test importing
	- Regression tests (compile all samples and compare new compiles against saved versions)
	- Performance tests (generate large grammar and query files)
- Create a vim syntax file for Mayhap grammars
