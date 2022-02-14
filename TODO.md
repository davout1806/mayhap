# TODO

- Multiple selection:
	- No spacing: `[3 * letter]`
	- List ("a, b, and c"): `[3 *& word]`
	- Custom separator: `[3 * '/' & number]` for a `/` separator
- Context-sensitive inflections:
	- Articles: `a[n] [animal]`
	- Pluralization: `[5-10] item[s]`
- Case:
	- Inherit case: `[symbol_name]`
	- Sentence case: `[Symbol_name]` or `[symbol_name!]`
	- Title case: `[Symbol_Name]` or `[symbol_name!!]`
	- Upper case: `[SYMBOL_NAME]` or `[symbol_name!!!]`
	- Limit symbol names to lowercase letters + underscores
- Force pluralization: `[thing+]`
- Parameterized rules: `greet(name)`, `Hi, $name!`, `[greet('Bob')]`
- Allow escaping blocks
