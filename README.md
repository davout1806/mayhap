# Mayhap

A grammar-based random text generator, inspired by [Perchance](https://perchance.org).

## Setup

Mayhap depends only on Python 3.

To install Mayhap, simply clone the repository.

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
Mayhap does not support the full range of features in Perchance grammars, but more are planned to be supported soon.

Note that Mayhap is not officially related to nor endorsed by Perchance, and merely takes inspiration from its syntax.

## Contributing

If you want to submit a PR, please follow these guidelines:

- Run the project on some samples to test for bugs.
- Run some Python linters such as Pylint, flake8, and/or mypy to help ensure consistent code style and quality.
- If you create any new Python source files, copy the license notice from `mayhap.py` into them.
