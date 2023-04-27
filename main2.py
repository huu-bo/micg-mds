from parser import parse, Token
from typing import List, Tuple, Union, Dict
from values import *
from values import Variable

# operator precedence
#  (TYPE) name
#  NAME.NAME            ['.', first, second]
#  f()                  ['f', function: str, args: list]
#  *= /=
#  * /
#  += -=
#  + -
#  =< => <== >== === !==
#  < > <= >= == !=

# '*', left, right


def expression(tokens: List[Token]):
    if len(tokens) == 1:
        return tokens[0]

    # i = 0
    # while i < len(tokens) - 3:
    #     if tokens[i][0] == 'NAME' and tokens[i + 1] == ['TOKEN', '(']:
    #         return ['FUNC', tokens[i][1]]
    #
    #     i += 1

    print('    |', tokens)

    t = []
    r = []
    for i, token in enumerate(tokens):
        if token == ['TOKEN', ',']:
            if t:
                r.append(expression(t))
                t = []
            else:
                pass  # TODO: this allows for e.g. print(, , , , , , , , , , "a\n");
        elif token == ['TOKEN', '(']:
            break
        else:
            t.append(token)
    if r:
        r.append(expression(t))

    if len(r) > 1:
        return r

    # i = 0
    # while i < len(tokens):
    #     if tokens[i] == ['TOKEN', ';'] and not i + 1 == len(tokens):
    #         return [expression(tokens[:i])] + [expression(tokens[i + 1:])]
    #     elif tokens[i] == ['TOKEN', ';']:
    #         return expression(tokens[:i])
    #     i += 1

    i = 0
    while i < len(tokens):
        if tokens[i] == ['TOKEN', '(']:
            # print(tokens[i:])
            # print(func_args(tokens[i:]))

            # print(            tokens[i + 1:func_args(tokens[i:]) + 3])
            # print( expression(tokens[i + 1:func_args(tokens[i:]) + 3]))
            args = expression(tokens[i + 1:func_args(tokens[i:]) + 3])
            if args is None:
                args = []
            elif type(args) == Token:
                args = [args]
            return 'f', expression(tokens[:i]), args
        i += 1

    i = 0
    level = 0
    while i < len(tokens):
        if tokens[i] == ['TOKEN', '(']:
            level += 1
        elif tokens[i] == ['TOKEN', ')']:
            level -= 1
        if not level:
            if tokens[i] == ['TOKEN', '.']:
                return '.', expression(tokens[:i]), expression(tokens[i + 1:])
        i += 1

    # TODO: () with math
    i = 0
    while i < len(tokens):
        if tokens[i] == ['TOKEN', '+']:
            return '+', expression(tokens[:i]), expression(tokens[i + 1:])
        elif tokens[i] == ['TOKEN', '-']:
            return '-', expression(tokens[:i]), expression(tokens[i + 1:])

        i += 1

    i = 0
    while i < len(tokens):
        if tokens[i] == ['TOKEN', '*']:
            return '*', expression(tokens[:i]), expression(tokens[i + 1:])
        elif tokens[i] == ['TOKEN', '/']:
            return '/', expression(tokens[:i]), expression(tokens[i + 1:])
        i += 1


def func_expression(tokens: List[Token]):
    r = []
    t = []
    for token in tokens:
        if token == ['TOKEN', ';']:
            r.append(expression(t))
            t = []
        else:
            t.append(token)

    if t:
        pass  # TODO: this means that the last line did not have a semicolon

    return r


def func_args(tokens: List[Token]):
    assert tokens[0] == ['TOKEN', '('], '????'
    level = 0
    for i in range(len(tokens)):
        if tokens[i] == ['TOKEN', '(']:
            level += 1
        elif tokens[i] == ['TOKEN', ')']:
            level -= 1
            if level == 0:
                return i

    if level:
        assert False, 'no function closing brace (level > 0)'
    else:
        assert False, 'no function closing brace (unexpected EOF)'


def error(tokens: list, i: int, text: str, msg: str, note: Union[Tuple[int, str, bool]] = None):  # TODO: an explanation in the error message
    print('\33[31m', end='')
    print(tokens[i:i + 7])
    # print(f'unknown syntax, line {tokens[i].line}')  # TODO: different kinds of error
    print(f'line {tokens[i].line}')

    j = tokens[i].index
    while j > 0 and text[j] != '\n':
        j -= 1
    spaces_amount = tokens[i].column
    j += 1
    print('\33[0m', end='')
    while j < len(text) and text[j] != '\n':
        print(text[j], end='')
        j += 1
    print('\33[31m')
    print(' ' * spaces_amount + '^' * len(tokens[i].data))

    print(msg)

    if note is not None:
        if len(note) != 3:
            raise ValueError('note should be (index: int, text: str, replace: bool)')

        if type(note[0]) != int:
            raise ValueError('note should be (index: int, text: str, replace: bool)')
        if type(note[1]) != str:
            raise ValueError('note should be (index: int, text: str, replace: bool)')
        if type(note[2]) != bool:
            raise ValueError('note should be (index: int, text: str, replace: bool)')

        print('\33[96mnote:')

        if note[2]:
            line = ''

            j = tokens[i].index
            while j > 0 and text[j] != '\n':
                j -= 1
            j += 1
            line_start = j
            print('\33[0m', end='')
            while j < len(text) and text[j] != '\n':
                line += text[j]
                j += 1
            spaces_amount = tokens[note[0]].column
            print(line)
            print('\33[96m' + ' ' * spaces_amount + '^' * len(tokens[i].data))
            print(' ' * spaces_amount + note[1])
        else:
            j = tokens[i].index
            while j > 0 and text[j] != '\n':
                j -= 1
            j += 1
            line_start = j
            print('\33[0m', end='')
            while j < len(text) and text[j] != '\n':
                print(text[j], end='')
                j += 1
            spaces_amount = j - line_start  # TODO: always places at the end of the line
            print('\33[96m' + note[1])
            print(' ' * spaces_amount + '^' * len(note[1]))

    exit(1)


# import Console as c;
# import Test;
# from Lib import func;
# from Console import print as p;
# {'c': ['library', 'Console'], 'Test': ['library', 'Test], 'func': [['library', 'Lib'], ['func', 'func']],
# 'p': [['library', 'Console'], ['func', 'print']}

# func int t(a: int) {}

def parse_text(tokens: List[Token], text: str):
    # constants
    #  also things like
    #   libraries
    #   functions
    #   @load
    constants: Dict[str, Union[Function, LibraryFunction, Library]] = {}
    variables = {}
    next_func = []  # things like @load on next function
    out = []
    i = 0
    while i < len(tokens):
        print(tokens[i:i + 20])
        if tokens[i] == ['STATEMENT', 'import']:
            # TODO: error messages
            assert tokens[i + 1].type == 'NAME'
            if tokens[i + 2] == ['STATEMENT', 'as']:  # import A as B;
                assert tokens[i + 3].type == 'NAME'
                assert tokens[i + 4] == ['TOKEN', ';']

                constants[tokens[i + 3].data] = Library(tokens[i + 1].data)

                i += 5
                continue
            elif tokens[i + 2] == ['TOKEN', ';']:  # import A;
                constants[tokens[i + 1].data] = Library(tokens[i + 1].data)
                i += 3
                continue
            else:
                assert False, 'expected semicolon'

        elif tokens[i] == ['STATEMENT', 'from']:
            if tokens[i + 1].type != 'NAME':
                error(tokens, i + 1, text, 'expected name')
            if tokens[i + 2] != ['STATEMENT', 'import']:
                error(tokens, i + 2, text, "expected 'import'", note=(i + 2, 'import', True))
            if tokens[i + 3].type != 'NAME':
                error(tokens, i + 3, text, 'expected name')

            if tokens[i + 4] == ['TOKEN', ';']:  # from A import B;
                constants[tokens[i + 3].data] = LibraryFunction(tokens[i + 3].data, tokens[i + 1])
                i += 4
            elif tokens[i + 4] == ['STATEMENT', 'as']:  # from A import B as C
                if tokens[i + 5] == ['TOKEN', '(']:  # from A import B as (...)
                    skip = func_args(tokens[i+5:])
                    body = tokens[i+6:i+5+skip]  # TODO: AST'ify
                    l = i+6+skip  # TODO: this is not func args but something like expression()
                    print('advanced import: ', tokens[i+5:l])

                    if tokens[l] == ['TOKEN', ';']:  # from A import B as (...)
                        name = tokens[i + 3].data
                        constants[name] = AdvancedLibraryFunction(name, body)
                        i = l
                    elif tokens[l + 2] == ['TOKEN', '(']:  # from A import B as (...) named C(...);
                        if tokens[l] != ['STATEMENT', 'named']:
                            error(tokens, l, text, "expected 'named'", note=(l, 'named', True))
                        if tokens[l + 1].type != 'NAME':
                            error(tokens, l + 1, text, 'expected name')  # TODO: information about what is a name and what not

                        name = tokens[l + 1].data
                        if tokens[l + 2] == ['TOKEN', '(']:  # from A import B as (...) named C(...);
                            l += 2
                            l += func_args(tokens[l:])  # TODO

                            if tokens[l + 1] != ['TOKEN', ';']:
                                error(tokens, l, text, "expected semicolon", note=(l+1, ';', False))

                            l += 1
                            i = l

                            constants[name] = AdvancedLibraryFunction(name, body)
                            # print(constants[name], constants[name].body)  # TODO: assert ';'
                            # raise NotImplementedError('from A import B as () named C();')  # implemented?
                    else:  # from A import B as (...) named C;
                        if tokens[l] != ['STATEMENT', 'named']:
                            error(tokens, l, text, '', (l, 'named', True))
                        if tokens[l + 1].type != 'NAME':
                            error(tokens, l + 1, text, 'expected name of func')
                        if tokens[l + 2] != ['TOKEN', ';']:
                            error(tokens, l + 1, text, 'expected semicolon', (0, ';', False))  # TODO: alignment broken

                        name = tokens[l + 1].data
                        constants[name] = AdvancedLibraryFunction(name, body)
                        i = l + 2

                        # raise NotImplementedError('from A import B as (...) named C;')
                else:  # from A import B as C;
                    if tokens[i + 5].type != 'NAME':
                        error(tokens, i + 5, text, 'expected name')
                    if tokens[i + 6] != ['TOKEN', ';']:
                        error(tokens, i + 5, text, 'expected semicolon', note=(0, ';', False))

                    constants[tokens[i + 5].data] = LibraryFunction(tokens[i + 3].data, tokens[i + 1].data)
                    # constants[tokens[i + 5].data] = [['library', tokens[i + 1].data], ['func', tokens[i + 3].data]]
                    i += 6
            else:
                assert False

        elif tokens[i] == ['TOKEN', '@']:
            assert tokens[i + 1].type == 'STATEMENT', "after '@' there should be 'load'"  # TODO more
            # assert not next_func, 'no'  # TODO: @private @load (yes)
            next_func.append(tokens[i + 1].data)
            i += 2
            continue

        # TODO
        elif tokens[i] == ['STATEMENT', 'func']:  # func
            if tokens[i + 1].type == 'NAME':
                if tokens[i + 2] == ['TOKEN', '(']:  # func NAME () {
                    skip, args = func_define(tokens[i + 3:])
                    name = tokens[i + 1].data

                    constants[name] = Function(name, 'void', args, next_func)
                    next_func = []

                    i += skip + 3
                    skip, body = func_body(tokens[i:])
                    constants[name].body = expression(body)
                    i += skip + 1
                    continue
                elif tokens[i + 2] == ['TOKEN', '{']:  # func NAME {
                    print('function', tokens[i + 1].data, [])
                    raise NotImplementedError('func NAME {')
                else:
                    assert False, 'incorrect function definition'
            elif tokens[i + 1].type == 'TYPE':  # func TYPE NAME () {
                if tokens[i + 2].type != 'NAME':
                    error(tokens, i + 2, text, 'invalid name')
                skip, args = func_define(tokens[i + 4:])
                name = tokens[i + 2].data
                ret_type = tokens[i + 1].data

                constants[name] = Function(name, ret_type, args, next_func)
                next_func = []

                i += skip + 4
                skip, body = func_body(tokens[i:])
                i += skip + 1
                continue
        elif tokens[i] == ['TOKEN', ';']:
            pass

        elif tokens[i].type == 'TYPE':
            types = []
            name = ''
            while i < len(tokens):
                if tokens[i].type == 'NAME':
                    name = tokens[i].data
                    break

                if tokens[i].type != 'TYPE':
                    error(tokens, i, text, 'there should be a type before a variable name')

                if tokens[i].data not in types:
                    types.append(tokens[i].data)
                # print(types)
                i += 1
            else:
                error(tokens, i-1, text, 'unexpected eof\nexpected variable name')

            assert tokens[i + 1] == ['TOKEN', ';'] or tokens[i + 1] == ['TOKEN', '='], "expected ';' or '='"

            if tokens[i + 1] == ['TOKEN', '=']:
                if 'final' in types:
                    assert tokens[i + 3] == ['TOKEN', ';'], 'expected semicolon after final TYPE NAME = VALUE'
                    constants[name] = Constant(name, types, tokens[i + 2])
                    i += 3
                    continue
                    # raise NotImplementedError('final variable')
                else:
                    assert tokens[i + 3] == ['TOKEN', ';'], 'SMEICOLCOON'
                    variables[name] = Variable(name, types, value=tokens[i + 2])
                    i += 3
                    continue
            else:
                if 'final' in types:
                    assert False, 'final variables should have a value'
                else:
                    assert tokens[i + 1] == ['TOKEN', ';'], 'SEMICOLON'
                    variables[name] = Variable(name, types)
                    i += 1
            # assert False

        else:
            print('\33[31m', end='')
            print(tokens[i:i + 7])
            print(f'unknown syntax, line {tokens[i].line}')

            j = tokens[i].index
            while j > 0 and text[j] != '\n':
                j -= 1
            spaces_amount = tokens[i].index - j - len(tokens[i].data) - 1
            j += 1
            print('\33[0m', end='')
            while j < len(text) and text[j] != '\n':
                print(text[j], end='')
                j += 1
            print('\33[31m')
            print(' ' * spaces_amount + '^' * len(tokens[i].data))
            # TODO: more help on what kind of exception this is and how to fix it
            exit(1)

        i += 1

    print('-' * 70)
    print(constants)
    print(variables)


def func_define(tokens: List[Token]) -> Tuple[int, List[str]]:
    print('[func]', tokens)
    if tokens[0] == ['TOKEN', ')']:
        return 1, []
    else:
        i = 0
        args = []
        comma = True
        while tokens[i] != ['TOKEN', ')']:
            if tokens[i] == ['TOKEN', ':']:
                raise NotImplementedError('type hints')
            if tokens[i] == ['TOKEN', ',']:
                if comma:
                    raise NotImplementedError('default value')
                comma = True
                i += 1
                continue
            assert tokens[i].type == 'NAME'
            comma = False
            args.append(tokens[i].data)
            i += 1
        return i + 1, args


def func_body(tokens: List[Token]) -> Tuple[int, List[Token]]:
    assert tokens[0] == ['TOKEN', '{'], 'function body not body but ' + "'" + str(tokens[0]) + "'"

    print('function body', tokens)

    i = 0
    body = []
    level = 0
    while i < len(tokens):
        if tokens[i] == ['TOKEN', '{']:
            level += 1
        if tokens[i] == ['TOKEN', '}']:
            level -= 1
            if level == 0:
                break
        body.append(tokens[i])

        i += 1
    else:
        assert False, 'function body has no end'

    return i, body


if __name__ == '__main__':
    with open('main.mds', 'r') as file:
        data = file.read()

    print(parse(data))
    parse_text(parse(data), data)

    # tokens = parse('1*(2+3); ')
    # t = []
    # for token in tokens:
    #     if token == ['TOKEN', ';']:
    #         print(expression(t))
    #         t = []
    #     else:
    #         t.append(token)
