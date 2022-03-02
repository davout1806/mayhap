# Mayhap

A grammar-based random text generator, inspired by [Perchance](https://perchance.org).

## Installation

Dependencies:

- Python 3
- [pyparsing](https://github.com/pyparsing/pyparsing)
- [inflect](https://github.com/jaraco/inflect) (optional; required for quality articles, plurals, and ordinals)

To install Mayhap, clone the repository and install the required dependencies by running:
```sh
pip install -r requirements.txt
```

## Usage

To run Mayhap, execute the following command:

```sh
./mayhap.py grammar.mh [pattern]
```

`grammar.mh` may be any Mayhap grammar file (see Grammars).
If a `pattern` is given, it will be expanded and printed to standard output.
If no `pattern` is given, patterns will be read line-by-line from standard input, and their expansions printed to standard output.

For detailed usage information, run:

```sh
./mayhap.py --help
```

### Grammars

Sample grammar files may be found in the `samples` directory.
Mayhap grammars follow a syntax similar to those of [Perchance](https://perchance.org/tutorial).
Mayhap does not support the full range of features in Perchance grammars, nor does it plan to, but more features are planned to be supported soon nonetheless.

Note that Mayhap is not affiliated with nor endorsed by Perchance, and merely takes inspiration from its syntax.

## Contributing

If you want to submit a PR, please follow these guidelines:

- Run `python3 -m unittest` to run the unit test suite.
- Run `test/test_samples.sh` to run Mayhap on all samples.
- Run some Python linters such as Pylint, flake8, and/or mypy to help ensure consistent code style and quality.
- If you create any new Python source files, copy the license notice from `mayhap.py` into them.
