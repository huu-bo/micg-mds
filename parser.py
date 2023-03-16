from typing import List


class Token:
    def __init__(self, t: str, data: str, pos: int):
        self.index = pos
        self.type = t
        self.data = data

    def __repr__(self):
        return "['" + self.type + "', '" + self.data + "']"

    def __eq__(self, other):
        if type(other) != list:
            return NotImplemented
        if len(other) != 2:
            raise TypeError
        if type(other[0]) != str:
            raise TypeError
        if type(other[1]) != str:
            raise TypeError

        return self.type == other[0] and self.data == other[1]


TOKENS = [
    '@',
    '(', ')',
    '{', '}',
    '$',
    ';',
    '.', ',',
    '=',

    '*', '/', '+', '-'
    '[', ']'
]
STATEMENTS = [
    'func',
    'import',
    'as',
    'from',
    'named',

    'load',
    'private'
]
TYPES = [
    'int',
    'void',
    'char',
    'range'

    # TODO: more data types
    #           something like rust range https://doc.rust-lang.org/std/ops/struct.Range.html
    #           hashmap
    #           classes
    #           interfaces
    #           tuples (type of tuple is like '(int, str)')

    # TODO: nullable data type or variable type?
    #       nullable int  a;
    #       nullable<int> a;
]
TYPE_MODS = [
    'unsigned',
    'final',
    'private'
]
TYPES += TYPE_MODS


FILE_SYNTAX = 0
CODE_SYNTAX = 1
BRACE_SYNTAX = 2


def token_type(string: str) -> Token:
    global i
    if string in TOKENS:
        return Token('TOKEN', string, i)
    elif string in STATEMENTS:
        return Token('STATEMENT', string, i)
    else:
        return Token('NAME', string, i)  # TODO: use name_type to make faster


def name_type(string: str) -> str:
    if string in TYPES:
        return 'TYPE'
    elif string.isdecimal():
        return 'INT_LIT'
    else:
        return 'NAME'


def parse(string: str):
    tokens: List[Token] = []

    t = ''
    incomment = False
    instring = False
    i = 0
    for c in string:
        if not incomment and not instring:
            if c == '\n':
                i += 1
                continue

            if c == ' ':
                if t:
                    tokens.append(token_type(t))
                    t = ''
            elif c == '"':
                if t:
                    tokens.append(token_type(t))
                    t = ''
                instring = True
            elif c == '/' and string[i + 1] == '/':
                if t:
                    tokens.append(token_type(t))
                incomment = True
            elif c in TOKENS:
                if t:
                    tokens.append(token_type(t))
                    t = ''
                tokens.append(Token('TOKEN', c, i))
            else:
                t += c

            if t in TOKENS:
                tokens.append(Token('TOKEN', t, i))
                t = ''
            elif t in STATEMENTS:
                tokens.append(Token('STATEMENT', t, i))
                t = ''
        elif incomment:
            if c == '\n':
                incomment = False
        elif instring:
            if c != '"':
                t += c
            else:
                tokens.append(Token('STR', t, i))
                t = ''
                instring = False

        # print(c, t)

        i += 1

    for i in range(len(tokens)):
        if tokens[i].type == 'NAME':
            tokens[i].type = name_type(tokens[i].data)
    for i in range(1, len(tokens)):
        if tokens[i] == ['STATEMENT', 'private'] and not tokens[i - 1] == ['TOKEN', '@']:
            tokens[i].type = 'TYPE'

    return tokens
