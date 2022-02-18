# TODO

- Ranges:
	- Alphabetic ranges: `[a-z]`, `[A-Z]`
	- Decimal ranges: `[0.5-2.5]` (output uses the same digits of precision as the more precise number in the range)
	- Ordinals: `[1-10.th]`
- Conditional pluralization: `[x=1-5] [item.s($x)]`
- Case:
	- Lower case: `[symbol]`
	- Title case: `[Symbol]`
	- Upper case: `[SYMBOL]`
- Patterns vs. blocks:
	- Special: all text in blocks (by default)
	- Pattern: double quotes
	- Literal: single quotes
	- Allow modifiers for patterns and literals
- Parameterized rules:
	- Symbol definition: `greet(name)`
	- Rule definition: `Hi, [$name]!`
	- Invocation: `[greet('Bob')]`
- Markov chains: `[name.markov]`
- Variable assignments:
	- Silent: `[variable = value]`
	- Echoed: `[$variable = value]`?
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
- Interactive mode:
	- Input prompts
	- Nicer formatting
	- Reuse the last input when a blank line is entered
- Consider removing `a(n)` and `(s)` in favor of `.a` and `.s()`
- Notify about syntax errors nicely rather than throwing raw Python exceptions
- Flag to control whether unused variables are reset between queries
- Make basic guesses at indefinite articles and plurals if inflect is not installed
- Syntax documentation/tutorial
- Test suite
	- Unit tests
	- Regression tests (compile all samples and compare new compiles against saved versions)
	- Benchmarking (generate large grammar and query files)
