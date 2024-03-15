# basic shunting yard parser
# reference: https://en.wikipedia.org/wiki/Shunting_yard_algorithm
from __future__ import annotations

import error
import lexer
from dataclasses import dataclass
from typing import Callable
# import ast
Token = lexer.Token


def is_int(s: Token):
    try:
        int(s.data)
        return True
    except ValueError:
        return False


@dataclass
class Node:
    operation: str
    children: 'list[Node | int]'

    def __repr__(self):
        c = '\n'.join('\n'.join('\t' + line for line in repr(child).splitlines()) for child in self.children)
        return f'{self.operation}\n{c}'


# tokens = ['1', '+', '2', '*', '3', '*', '4']
# tokens = ['1', '*', '2', '+', '3']
# tokens = ['1', '+', '2', '-', '3']
# tokens = ['(', '1', '+', '2', ')', '^', '3']
# tokens = ['print', '(', '1', '+', '1', ',', '2', ')']
# tokens = ['1', '+', 'print', '(', '1', '+', '1', ',', 'print', '(', '2', ')', ',', '3', ')', '+', '2']
tokens = lexer.lex('1 + print(1 + 1, print(2), 3) + 2 ')
# tokens = lexer.lex('1 + 2 * 3 + 4 ')

asso = {'callfunc': 5, '+': 2, '-': 2, '*': 3, '/': 3, '^': 4}
asso_dir = {'+': 'left', '-': 'left', '*': 'left', '/': 'left', '^': 'right'}
functions = {'print'}

# Operator 	Precedence 	Associativity
# ^         4           Right
# ×         3           Left
# ÷         3           Left
# +         2           Left
# −         2           Left


def expect(data: str | None = None, type_: str | None = None) -> Token:
    global tokens

    if data is None and type_ is None:
        raise ValueError('Either data or type_ must be provided')

    t = tokens.pop(0)
    if type_ is not None and t.type != type_:
        raise SyntaxError(f'{type_} != {t.type} @ {t.index}')
    if data is not None and t.data != data:
        raise SyntaxError(f'{data} != {t.data} @ {t.index}')

    return t


def accept(data: str | None = None, type_: str | None = None, inc: bool = True) -> bool:
    global tokens

    if not tokens:
        return False

    if data is None and type_ is None:
        raise ValueError('Either data or type_ must be provided')

    t = tokens[0]
    if type_ is not None and t.type != type_:
        return False
    if data is not None and t.data != data:
        return False

    if inc:
        tokens.pop(0)
    return True


# def expr() -> Node:
#     if is_int()


line = '-' * 20

print('tokens:', tokens)

print(line, 'parsing')


def _op(ops: list[str], next_: Callable[[], Node | int]) -> Node | int:
    lhs = next_()
    while True:
        op = None
        for o in ops:
            if accept(data=o):
                op = o

                if op is None:
                    raise ValueError
                break

        if op is not None:
            rhs = next_()
            lhs = Node(op, [lhs, rhs])
        else:
            return lhs


def addition() -> Node | int:
    return _op(['+', '-'], multiplication)


def multiplication() -> Node | int:
    return _op(['*', '/'], parenthesis)


def parenthesis() -> Node | int:
    if accept(data='('):
        res = addition()
        expect(data=')')
        return res
    else:
        return function()


def function() -> Node | int:
    if accept(type_='NAME', inc=False):
        f = expect(type_='NAME')

        expect(data='(')

        values = [addition()]
        while accept(data=','):
            values.append(addition())

        expect(data=')')
        return Node('call', [f.data] + values)
    else:
        return negation()


def negation() -> Node | int:
    if accept(data='-'):
        return Node('neg', [parenthesis()])
    else:
        return value()


def value() -> Node | int:
    return int(expect(type_='INT_LIT').data)


print(addition())
