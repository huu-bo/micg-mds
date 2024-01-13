import typing

import json

TOKENS = [
    '@',
    '(', ')',
    '{', '}',
    '$',
    ';',
    '.', ',',

    '*', '/', '+', '-'
]
STATEMENTS = [
    'func',
    'import',
    'as',
    'load'
]
TYPES = [
    'int'
]


FILE_SYNTAX = 0
CODE_SYNTAX = 1
BRACE_SYNTAX = 2


def token_type(string: str) -> list:
    if string in TOKENS:
        return ['TOKEN', string]
    elif string in STATEMENTS:
        return ['STATEMENT', string]
    else:
        return ['NAME', string]


def name_type(string: str) -> str:
    if string in TYPES:
        return 'TYPE'
    elif string.isdecimal():
        return 'INT_LIT'
    else:
        return 'NAME'


def parse(string: str):  # TODO: accepteer spaties
    tokens = []

    t = ''
    incomment = False
    instring = False
    i = 0
    for c in string:
        if not incomment and not instring:
            if c == '\n':
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
            elif c in TOKENS:
                if t:
                    tokens.append(['NAME', t])
                    t = ''
                tokens.append(['TOKEN', c])
            elif c == '/' and string[i + 1] == '/':
                if t:
                    tokens.append(['NAME', t])
                incomment = True
            else:
                t += c

            if t in TOKENS:
                tokens.append(['TOKEN', t])
                t = ''
            elif t in STATEMENTS:
                tokens.append(['STATEMENT', t])
                t = ''
        elif incomment:
            if c == '\n':
                incomment = False
        elif instring:
            if c != '"':
                t += c
            else:
                tokens.append(['STR', t])
                t = ''
                instring = False

        # print(c, t)

        i += 1

    for i in range(len(tokens)):
        if tokens[i][0] == 'NAME':
            tokens[i][0] = name_type(tokens[i][1])

    return tokens


def matches(t, syntax) -> tuple:
    for s in syntax:
        i = 0
        match = True
        for token in t:
            if i < len(s[0]):
                # print(s[0][i], t[i][0], t[i][1], s[0][i] != t[i][0] and s[0][i] != t[i][1])
                if s[0][i] != t[i][0] and s[0][i] != t[i][1]:
                    match = False
            # else:
            #     match = False
            i += 1
        # print(t, s[0], match, len(t), len(s[0]))
        if match and len(t) == len(s[0]):
            return True, s[1]
    return False, 0


# def parse_code(tokens):
#     assert tokens[0][1] == '{'

def parse_code(tokens):
    with open('syntax.json', 'r') as file:
        syntax = json.load(file)[1]

    t = []
    p = []
    out = []
    for token in tokens:
        match = matches(t, syntax)
        print(match, t)
        if match[0]:
            print(match, t)
            out.append(match[1])
            t = []
        elif token[1] == '{':
            parse2(tokens[tokens.index(token):])
        elif token[1] == '}':
            pass
        t.append(token)


# {'c': ['library', 'Console'], 'Console': ['library', 'Console]}


def parse2(tokens: list):
    # constants
    #  also things like
    #   libraries
    #   functions
    #   @load
    constants = {}
    next_func = ''  # things like @load on next function
    out = []
    i = 0
    while i < len(tokens):
        print(tokens[i:i+5])
        if tokens[i] == ['STATEMENT', 'import']:
            # TODO: error messages
            assert tokens[i + 1][0] == 'NAME'
            if tokens[i + 2] == ['STATEMENT', 'as']:
                assert tokens[i + 3][0] == 'NAME'
                assert tokens[i + 4] == ['TOKEN', ';']

                constants[tokens[i + 3][1]] = ['library', tokens[i + 1][1]]

                i += 5
                continue
            elif tokens[i + 2] == ['TOKEN', ';']:
                constants[tokens[i + 1][1]] = ['library', tokens[i + 1][1]]
                i += 3
                continue
            else:
                assert False, 'expected semicolon'

        elif tokens[i] == ['TOKEN', '@']:
            assert tokens[i + 1][0] == 'STATEMENT', "after '@' there should be 'load'"  # TODO more
            assert not next_func, 'no'
            next_func = tokens[i + 1][1]
            i += 2
            continue

        elif tokens[i] == ['STATEMENT', 'func']:
            assert tokens[i + 1][0] == 'NAME', 'please give valid name as function name'

            if tokens[i + 2] == ['TOKEN', '(']:
                print(func_define(tokens[i+3:]))
            elif tokens[i + 2] == ['TOKEN', '{']:
                raise NotImplementedError
            else:
                assert False, 'incorrect function definition'

        else:
            print(tokens[i:i+7])
            assert False, 'unknown syntax'

        i += 1

    print(constants)


def func_define(tokens: list) -> typing.Tuple[int, list]:  # TODO: better typing
    if tokens[0] == ['TOKEN', ')']:
        return 0, []

    out = []
    i = 0
    comma = True
    while tokens[i] != ['TOKEN', ')']:
        if tokens[i][0] == 'NAME':
            assert comma, 'expected comma between function parameters'
            out.append(tokens[i][1])
            comma = False
        elif tokens[i] == ['TOKEN', ',']:
            comma = True
        else:
            raise SyntaxError(f'unexpected token {tokens[i]} in function declaration')
        i += 1


if __name__ == '__main__':
    with open('main.mds', 'r') as file:
        data = file.read()

    print(parse(data))
    parse2(parse(data))
