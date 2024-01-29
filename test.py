# basic shunting yard parser
# reference: https://en.wikipedia.org/wiki/Shunting_yard_algorithm

import error
import lexer
Token = lexer.Token


def is_int(s: Token):
    try:
        int(s.data)
        return True
    except ValueError:
        return False


# tokens = ['1', '+', '2', '*', '3', '*', '4']
# tokens = ['1', '*', '2', '+', '3']
# tokens = ['1', '+', '2', '-', '3']
# tokens = ['(', '1', '+', '2', ')', '^', '3']
# tokens = ['print', '(', '1', '+', '1', ',', '2', ')']
# tokens = ['1', '+', 'print', '(', '1', '+', '1', ',', 'print', '(', '2', ')', ',', '3', ')', '+', '2']
# tokens = lexer.lex('1 + print(1 + 1, print(2), 3) + 2')
tokens = lexer.lex('1 + - 1 * 1')

asso = {'callfunc': 5, '+': 2, '-': 2, '*': 3, '/': 3, '^': 4}
asso_dir = {'+': 'left', '-': 'left', '*': 'left', '/': 'left', '^': 'right'}
functions = {'print'}

# Operator 	Precedence 	Associativity
# ^         4           Right
# ×         3           Left
# ÷         3           Left
# +         2           Left
# −         2           Left

output = []
operator = []
for token in tokens:
    if is_int(token):
        output.append(token)
    # elif token == ['TOKEN', ';']:
    #     if len(operator) != 0:
    #         raise SyntaxError(operator)
    elif token == ['TOKEN', '(']:
        operator.append(token)
    elif token == ['TOKEN', ')']:
        try:
            while operator[-1] != ['TOKEN', '(']:
                output.append(operator.pop())
            operator.pop()
        except IndexError:
            raise SyntaxError("expected '('")
        if len(operator) >= 1 and operator[-1] in functions:
            output.append(operator.pop())
    elif token.data in functions:
        output.append(token)
        operator.append('callfunc')
    elif token == ['TOKEN', ',']:
        try:
            while operator[-1] != ['TOKEN', '(']:
                output.append(operator.pop())
        except IndexError:
            raise SyntaxError("expected '('")
    else:
        operator.append(token)

        while (
                len(operator) >= 2
                and operator[-2] != ['TOKEN', '(']
                and operator[-2] != 'callfunc'
                and (
                        asso[operator[-1].data] < asso[operator[-2].data]
                        or (
                                asso[operator[-1].data] == asso[operator[-2].data]
                                and asso_dir[operator[-1].data] == 'left'
                        )
                )
        ):
            output.append(operator.pop(-2))

    # print(operator)
    print(output, operator)

if '(' in operator:
    raise SyntaxError("expected ')'")

output += reversed(operator)
print(output)

# stack = []
# for token in output:
#     if is_int(token):
#         stack.append(token)
#     elif token == 'callfunc':
#         # stack.append(token)
#         i = 0
#         removed = []
#         while stack[-1] not in functions:
#             i += 1
#             removed.append(stack.pop())
#         stack.pop()
#         stack += removed
#         stack.append(i)
#         stack.append(token)
#     elif token in functions:
#         stack.append(token)
#     elif (is_int(stack[-1]) or stack[-1] == 'node') and (is_int(stack[-2] or stack[-2] == 'node')):
#         stack.pop()
#         stack.pop()
#         stack.append('node')
#     else:
#         stack.append(token)
#
#     print(stack)
