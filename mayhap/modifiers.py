import re
import typing

from .common import MayhapError


try:
    import inflect
    INFLECT: typing.Optional[inflect.engine] = inflect.engine()
except ImportError:
    INFLECT = None


# Do not require a unique production to be chosen from the given symbol
MOD_MUNDANE = 'mundane'

# Add a context-sensitive indefinite article before this symbol
MOD_ARTICLE = 'a'

# Pluralize this symbol
MOD_PLURAL = 's'

# Convert this number to an ordinal (e.g. 1st, 10th)
MOD_ORDINAL = 'th'

# Capitalize the first letter of the first word
MOD_CAPITALIZE = 'capitalize'

# Convert to lowercase
MOD_LOWER = 'lower'

# Convert to upper case
MOD_UPPER = 'upper'

# Convert to title case (capitalize the first letter of each word)
MOD_TITLE = 'title'

MODIFIERS = set((
    MOD_MUNDANE,
    MOD_ARTICLE,
    MOD_PLURAL,
    MOD_ORDINAL,
    MOD_CAPITALIZE,
    MOD_LOWER,
    MOD_UPPER,
    MOD_TITLE,
))

# Matches dynamic pluralization
# e.g. (s)
RE_PLURAL = re.compile(r'\((s)\)', re.IGNORECASE)


def get_article(word):
    if INFLECT:
        return INFLECT.a(word).split()[0]
    if word and word[0] in 'aeiou':
        return 'an'
    return 'a'


def add_article(word):
    if INFLECT:
        return INFLECT.a(word)
    return get_article(word) + ' ' + word


def get_plural(word, number=None):
    if INFLECT:
        if number is not None:
            return INFLECT.plural(word, number)
        return INFLECT.plural(word)
    if number is not None and number == 1:
        return word
    return word + 's'


def resolve_plurals(pattern):
    output = ''
    last_match = 0
    for match in RE_PLURAL.finditer(pattern):
        # Find the previous number
        previous_word = ''
        previous_number = ''
        building_word = True
        for offset, character in enumerate(pattern[match.start() - 1::-1]):
            if building_word:
                if character.isalpha():
                    previous_word = character + previous_word
                    continue
                previous_word_start = match.start() - offset
                building_word = False
            if (character.isdigit() or
                    (previous_number and
                        character in '-.' and
                        previous_number[0] not in '-.')):
                previous_number = character + previous_number
            elif previous_number:
                break

        if previous_word:
            output += pattern[last_match:previous_word_start]

            if previous_number:
                if '.' in previous_number:
                    previous_number = float(previous_number)
                else:
                    previous_number = int(previous_number)

                previous_word = get_plural(previous_word, previous_number)
            else:
                previous_word = get_plural(previous_word)

            output += previous_word
        else:
            output += pattern[last_match:match.start()]
            output += match[1]

        last_match = match.end()
    output += pattern[last_match:]
    return output


def get_ordinal(number):
    if INFLECT:
        return INFLECT.ordinal(number)
    if number.isdigit():
        last_digit = int(number) % 10
        if last_digit == 1:
            return f'{number}st'
        if last_digit == 2:
            return f'{number}nd'
        if last_digit == 3:
            return f'{number}rd'
    return f'{number}th'


def apply_modifier(string, modifier):
    if modifier == MOD_PLURAL:
        return get_plural(string)
    if modifier == MOD_ARTICLE:
        return add_article(string)
    if modifier == MOD_ORDINAL:
        return get_ordinal(string)
    if modifier == MOD_CAPITALIZE:
        return string.capitalize()
    if modifier == MOD_LOWER:
        return string.lower()
    if modifier == MOD_UPPER:
        return string.upper()
    if modifier == MOD_TITLE:
        return string.title()
    if modifier == MOD_MUNDANE:
        return string
    raise MayhapError(f'Unknown modifier "{modifier}"')
