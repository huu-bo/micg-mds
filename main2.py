from parser import parse, Token
from typing import List, Tuple, Union, Dict
from constants import Function, LibraryFunction, Library

# operator precedence
#  f()
#  * /
#  + -
#  < > <= >= == !=

# '*', left, right
# ['FUNC', name], decorators|None, body


def expression(tokens: List[Token]):
    if len(tokens) == 1:
        return tokens[0]

    # i = 0
    # while i < len(tokens) - 3:
    #     if tokens[i][0] == 'NAME' and tokens[i + 1] == ['TOKEN', '(']:
    #         return ['FUNC', tokens[i][1]]
    #
    #     i += 1

    i = 0
    while i < len(tokens):
        if tokens[i] == ['TOKEN', '*']:
            return '*', expression(tokens[:i]), expression(tokens[i + 1:])
        elif tokens[i] == ['TOKEN', '/']:
            return '/', expression(tokens[:i]), expression(tokens[i + 1:])
        i += 1

    i = 0
    while i < len(tokens):
        if tokens[i] == ['TOKEN', '+']:
            return '+', expression(tokens[:i]), expression(tokens[i + 1:])
        elif tokens[i] == ['TOKEN', '+']:
            return '-', expression(tokens[:i]), expression(tokens[i + 1:])

        i += 1


# import Console as c;
# import Test;
# from Lib import func;
# from Console import print as p;
# {'c': ['library', 'Console'], 'Test': ['library', 'Test], 'func': [['library', 'Lib'], ['func', 'func']],
# 'p': [['library', 'Console'], ['func', 'print']}

# func int t(a: int) {}

def parse_text(tokens: List[Token]):
    # constants
    #  also things like
    #   libraries
    #   functions
    #   @load
    constants: Dict[str, Union[Function, LibraryFunction, Library]] = {}
    variables = []
    next_func = []  # things like @load on next function
    out = []
    i = 0
    while i < len(tokens):
        print(tokens[i:i + 5])
        if tokens[i] == ['STATEMENT', 'import']:
            # TODO: error messages
            assert tokens[i + 1].type == 'NAME'
            if tokens[i + 2] == ['STATEMENT', 'as']:  # import A as B;
                assert tokens[i + 3].type == 'NAME'
                assert tokens[i + 4] == ['TOKEN', ';']

                constants[tokens[i + 3].data] = ['library', tokens[i + 1].data]

                i += 5
                continue
            elif tokens[i + 2] == ['TOKEN', ';']:  # import A;
                constants[tokens[i + 1].data] = ['library', tokens[i + 1].data]
                i += 3
                continue
            else:
                assert False, 'expected semicolon'

        elif tokens[i] == ['STATEMENT', 'from']:
            assert tokens[i + 1].type == 'NAME'
            assert tokens[i + 2] == ['STATEMENT', 'import']

            if tokens[i + 4] == ['TOKEN', ';']:  # from A import B;
                constants[tokens[i + 3].data] = [['library', tokens[i + 1].data], ['func', tokens[i + 3].data]]
                i += 4
            elif tokens[i + 4] == ['STATEMENT', 'as']:  # from A import B as C;
                assert tokens[i + 5].type == 'NAME'
                assert tokens[i + 6] == ['TOKEN', ';']

                constants[tokens[i + 5].data] = [['library', tokens[i + 1].data], ['func', tokens[i + 3].data]]
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
        elif tokens[i] == ['STATEMENT', 'func']:
            if tokens[i + 1].type == 'NAME':
                if tokens[i + 2] == ['TOKEN', '(']:  # func NAME () {
                    skip, args = func_define(tokens[i + 3:])
                    name = tokens[i + 1].data

                    constants[name] = Function(name, 'void', args, next_func)
                    next_func = []

                    i += skip + 3
                    skip, body = func_body(tokens[i:])
                    i += skip + 1
                    continue
                elif tokens[i + 2] == ['TOKEN', '{']:  # func NAME {
                    print('function', tokens[i + 1].data, [])
                    raise NotImplementedError('func NAME {')
                else:
                    assert False, 'incorrect function definition'
            elif tokens[i + 1].type == 'TYPE':
                assert tokens[i + 2].type == 'NAME', 'please give valid name as function definition'
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
            while i < len(tokens):
                if tokens[i].type == 'NAME':
                    raise NotImplementedError('giving variable a name lol')
                assert tokens[i].type == 'TYPE', 'not type before variable name'

                if tokens[i].data not in types:
                    types.append(tokens[i].data)
                print(types)
                i += 1

            print(types)
            assert False

        else:
            print(tokens[i:i + 7])
            assert False, 'unknown syntax'

        i += 1

    print(constants)


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


def func_body(tokens: List[Token]) -> Tuple[int, list]:
    assert tokens[0] == ['TOKEN', '{'], 'function body not body but ' + "'" + str(tokens[0]) + "'"

    print('function body', tokens)

    i = 0
    while i < len(tokens):
        if tokens[i] == ['TOKEN', '}']:
            break

        i += 1
    else:
        assert False, 'function body has no end'

    return i, []


if __name__ == '__main__':
    with open('main.mds', 'r') as file:
        data = file.read()

    print(parse(data))
    parse_text(parse(data))
