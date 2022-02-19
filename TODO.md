# TODO

- Ranges:
	- Decimal ranges: `[0.5-2.5]` (output uses the same digits of precision as the more precise number in the range)
	- Dice parsing: `[2d6+3]`?
- Fractional weights `^2/5.5`
- Repeated accesses: `[5 * [0-9]]`
- Conditional pluralization: `[x=1-5] [item.s($x)]`
- Case:
	- Lower case: `[symbol]`
	- Title case: `[Symbol]`
	- Upper case: `[SYMBOL]`
	- Limit symbol and variable names to alphanumeric and underscores, starting with a letter
- Patterns vs. blocks:
	- Special: all text in blocks (by default)
	- Pattern: double quotes
	- Literal: single quotes
	- Allow modifiers for patterns and literals
- Local variable scoping
- Parameterized rules:
	- Symbol definition: `greet(name)`
	- Rule definition: `Hi, [$name]!`
	- Invocation: `[greet('Bob')]`
- Markov chains: `@markov symbolname`?
- Default output: `@default symbolname`?
- Escape characters:
	- Intentional leading/trailing whitespace: `\ my rule \ ^2`
	- Blocks: `\[not a block\]`
	- a: `a\(n\)`
	- s: `\(s\)`
	- Weights: `\^not a weight`
	- Standard escapes: `\n`, `\t`, `\\`

	  ```py
	  my_string.encode('raw_unicode_escape').decode('unicode_escape')`
	  ```
- Add syntax to reference symbols rather than having to evaluate them as strings
	- Symbol reference: `[x = &symbol]`
	- Symbol dereference: `[$x]` (chooses a different production for symbol each time `x` is accessed)
	- (Current workaround: `[x ~= 'symbol'][[$x]]`)
- C-style format string support: `['%02d' % [0-60]]`
- Consider removing `a(n)` and `(s)` in favor of `.a` and `.s()` (when implemented)
- Query [corpora](https://github.com/aparrish/pycorpora) and other sources for common data
- Flag to control whether unused variables are reset between queries (`persistent`)
- Shell commands
	- Show grammar: `/grammar`
	- Import another grammar: `/import path_to_grammar.mh`
	- Save grammar to file: `/export path_to_grammar.mh`
	- Add symbol: `/add symbol_name`
	- Add rule: `/add symbol_name rule_name`
	- Remove symbol: `/remove symbol_name`
	- Remove rule: `/remove symbol_name rule_name`
	- Toggle generator flags: `/set verbose`/`/unset verbose` or `/set verbose true`
- Run file as shell script (use `Cmd` but disable prompt)
- Argument to print "compiled" grammar
- Syntax documentation/tutorial
- Test suite
	- Unit tests
	- Regression tests (compile all samples and compare new compiles against saved versions)
	- Benchmarking (generate large grammar and query files)
