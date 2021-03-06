# TODO

## Grammar Features

- Use `pyparsing` to parse grammars as well as rules
- Ranges:
	- Decimal ranges: `[0.5-2.5]` (output uses the same digits of precision as the more precise number in the range)
	- Dice parsing: `[2d6+3]`
		- Regex: `(\d+)d(\d+)([+-](\d+)d(\d+))*([+-]\d+)?`
		- `dice` module
- Repeated accesses: `[5 * 0-9]`
- C-style format strings: `['%02d %s' % 0-60, b='test,']`
- Inflections:
	- Conditional pluralization: `[x=1-5] [item.s($x)]`
		- Will need a `ModifierToken` class to handle arguments
		- Modifier types could be made into classes that store their valid argument counts
		- Remove `(s)` when implemented
	- Present participle: `[verb.ing]`
		- `inflect.present_participle`
	- Pronouns:
		- `[gender = 'masculine'|'feminine'|'gender-neutral'|'neuter']` (taken directly from `inflect`)
		- `['they'.gender($g)]`, etc.
		- Use `inflect.gender` and `inflect.singular_noun`
	- Tense: `[verb.ed]`, etc.
		- https://github.com/WZBSocialScienceCenter/patternlite (unfortunately still fairly heavyweight)
		- Just make a basic custom implementation
- Parameterized rules:
	- Symbol definition: `greet(name)`
	- Rule definition: `Hi, [$name]!`
	- Invocation: `[greet('Bob')]`
	- Will need a `Symbol` class, hashable by its symbol name
- Symbol referencing:
	- Symbol reference: `[x = &symbol]`
		- `&symbol` will be parsed as a `ReferenceToken`
		- Validator will confirm that `symbol` is a valid symbol
		- Then, it will be converted to the literal `'symbol'`
	- Symbol dereference: `[*x]`
		- Parses as a `DereferenceToken`
		- Produces a random rule from the symbol named `'symbol'` (equivalent to the old `[[x]]`)
		- Validator will track all assignments to `x`, and warn/fail if `x` is ever assigned a non-`ReferenceToken` value
- Markov chains: `[name.markov]`
	- Validator will ensure that `name`'s rules are exclusively strings
	- `markov` modifier will be undefined for non-reference, non-symbol types
- Importing text files (files that start with a rule, not a symbol)
	- Import the file as a single symbol
	- The symbol name is the file name
	- Each line is a rule of the symbol
- Importing:
	- Default namespace: `import "../local"`
	- Custom namespace: `import "long_named_grammar" as lng`
	- No namespace (current implementation): `source "my_grammar"`
	- Usage: `[namespace:symbol]`
- Create a standard library of data/generators
	- Include as data files in `setup.cfg`
	- Import with `import <my_standard_grammar>`
- Default symbols:
	- The default symbol is the symbol with the same name as the file, or the last symbol if no symbol matches the file name
	- Use default symbol from namespace: `[namespace:]`
	- `[:]` could function as the default for the current file?
- Scoping:
	- Local symbol: `_symbol`
		- Not accessible when imported
	- Local variable: `$_local`
		- Useful for recursive symbols with unique variables at each depth
		- Save locals as a separate dictionary on the stack, copying it at each level
- Treat numbers as literal by default and store as numbers in variable dict
- Math/boolean expressions: `[(2 * a if a else 1)]`
	- https://github.com/danthedeckie/simpleeval
	- Use variables dict as `names` in `simple_eval` (no `$`)
	- Convert numeric output to `str`
	- Convert boolean output to `0` or `1` (for more direct translation to weight)
- Variable weight: `^[$weight]`, `^[(location == 'desert')]`, etc.
	- Change the weight rule to accept a number or a block and parse accordingly
	- Disallow assignments
	- Make symbol references default to mundane
- Symbols must end in `:`
- Enforce consistent indentation whitespace throughout the file and disallow mixed indent (spaces and tabs in same line)
- Ensure that `\ ` is defined
- Don't parse choices as rules, but as specials
	- Less convenient to write (`['a'|'b']` as opposed to `[a|b]`)
	- Discourages overly complex inline choices that should be separate symbols instead
	- Consistent with other in-block tokens (e.g. ignores whitespace)
	- Basic weight manipulation can be done by adding blank rules: `[rare|||]`
- A `Grammar` class may finally be useful to track variable names, Markov-able symbols, recursive symbols, etc.

## Program Features

- Warn to `stderr` when running out of unique symbols
- Flags
	- Make symbols default to mundane (`mundane`, false by default)
	- Maximum recursion depth for recursive symbols (important if `mundane` option is set)
- Arguments
	- Enable/disable optimizations
	- Print standardized grammar (fix `__str__` methods to print valid grammar, then just output `grammar_to_string`)
- Shell commands
	- Save grammar to file: `/export path_to_grammar.mh`
	- Toggle generator flags: `/set verbose`/`/unset verbose` or `/set verbose true`
- Improve autocomplete and fix autocomplete for help
- Run file as shell script (use `Cmd` but disable prompt)

## Non-Functional

- Syntax documentation/tutorial
- Test suite
	- Modifiers
	- Importing
	- Test with and without optimizations
	- Regression tests (compile all samples and compare new compiles against saved versions)
	- Performance tests (generate large grammar and query files)
- Create a vim syntax file for Mayhap grammars
