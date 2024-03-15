from __future__ import annotations

from typing import List

i = 0
line = 1
column = 0


class Token_builder:
    def __init__(self, data='', line_=None, column_=None, i_=None):
        global line, column, i
        if line_ is None:
            line_ = line
        if column_ is None:
            column_ = column
        if i_ is None:
            i_ = i

        self.data: str = data
        self.line: int = line_
        self.column: int = column_
        self.index: int = i_

    def __repr__(self):
        return f"[Builder '{self.data}']"


class Token:
    def __init__(self, type_: str, token: Token_builder):
        self.index = token.index
        self.type = type_
        self.data = token.data

        self.line = token.line
        self.column = token.column

    def __repr__(self):
        return "['" + self.type + "', '" + self.data + "']"

    def __eq__(self, other):
        if type(other) != list:
            raise TypeError
        if len(other) != 2:
            raise TypeError
        if type(other[0]) != str:
            raise TypeError
        if type(other[1]) != str:
            raise TypeError

        if other[1] == 'TYPE':  # temporary
            raise ValueError

        return self.type == other[0] and self.data == other[1]


TOKENS = [
    '@',
    '(', ')',
    '{', '}',
    '$',
    ';',
    '.', ',',
    '=',

    '*', '/', '+', '-',
    '[', ']'
]
STATEMENTS = [
    'func',
    'import',
    'as',
    'from',
    'named',

    'load',
    'private',

    'for'
]
# TODO: more data types
#           something like rust range https://doc.rust-lang.org/std/ops/struct.Range.html
#           hashmap
#           classes
#           interfaces
#           tuples (type of tuple is like '(int, str)')

# TODO: nullable data type or variable type?
#       nullable int  a;
#       nullable<int> a;


FILE_SYNTAX = 0
CODE_SYNTAX = 1
BRACE_SYNTAX = 2


def token_type(token: Token_builder) -> Token:
    global i
    if token.data in TOKENS:
        return Token('TOKEN', token)
    elif token in STATEMENTS:
        return Token('STATEMENT', token)
    else:
        return Token('NAME', token)  # TODO: use name_type to make faster


def name_type(string: str) -> str:
    if string.isdecimal():
        return 'INT_LIT'
    # elif string == '??!??!':  # deprecated, use '?'
    #     return 'TOKEN'
    else:
        return 'NAME'


def lex_number(string: str) -> int | float:
    try:
        return int(string)
    except ValueError:
        return float(string)


def lex(string: str) -> List[Token]:
    global i
    i = 0

    tokens: List[Token] = []

    global line, column
    line = 1
    column = 0

    t: Token_builder = Token_builder()
    incomment = False
    instring = False
    for c in string:
        if not incomment and not instring:
            if c == '\n':
                line += 1
                column = 0
                i += 1

                t = Token_builder()
                continue

            if c == ' ':
                if t.data:
                    tokens.append(token_type(t))
                t = Token_builder(column_=column+1)
            elif c == '"':
                if t.data:
                    tokens.append(token_type(t))
                t = Token_builder()
                instring = True
            elif c == '/' and string[i + 1] == '/':
                if t.data:
                    tokens.append(token_type(t))
                t = Token_builder()
                incomment = True
            elif c in TOKENS:
                if t.data:
                    tokens.append(token_type(t))
                t = Token_builder(column_=column+1)
                tokens.append(Token('TOKEN', Token_builder(data=c)))
            else:
                t.data += c

            if t.data in TOKENS:
                tokens.append(Token('TOKEN', t))
                t = Token_builder(column_=column+1)
            elif t.data in STATEMENTS:
                tokens.append(Token('STATEMENT', t))
                t = Token_builder(column_=column+1)
        elif incomment:
            if c == '\n':
                incomment = False
                line += 1
                column = 0
        elif instring:
            if c == '\n':
                line += 1
                column = 0

            if c != '"':
                t.data += c
            else:
                tokens.append(Token('STR', t))
                t = Token_builder()
                instring = False

        # print(c, t)

        i += 1
        column += 1

    for i in range(len(tokens)):
        if tokens[i].type == 'NAME':
            tokens[i].type = name_type(tokens[i].data)
    for i in range(1, len(tokens)):
        if tokens[i] == ['STATEMENT', 'private'] and not tokens[i - 1] == ['TOKEN', '@']:
            tokens[i].type = 'TYPE'

    return tokens


if __name__ == '__main__':
    def _test_parse(text: str, expect: list):
        tokens = lex(text)
        assert tokens == expect, f'{tokens} != {expect}'

    def _test_index(text: str, expect: list):
        tokens = lex(text)
        for i, token in enumerate(tokens):
            assert token.line == expect[i][0], f'line {token.line} != {expect[i]} @ {token} {i}'
            assert token.column == expect[i][1], f'column {token.column} != {expect[i]} @ {token} {i}'

    _test_parse('print(a);', [['NAME', 'print'], ['TOKEN', '('], ['NAME', 'a'], ['TOKEN', ')'], ['TOKEN', ';']])
    _test_parse('from a import b;',
                [['STATEMENT', 'from'], ['NAME', 'a'], ['STATEMENT', 'import'], ['NAME', 'b'], ['TOKEN', ';']])
    # TODO: test edge-cases

    _test_index('print(a);\ntest;', [[1, 0], [1, 5], [1, 6], [1, 7], [1, 8], [2, 0], [2, 4]])
