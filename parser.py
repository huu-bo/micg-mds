from __future__ import annotations

from typing import Callable

from lexer import Token, lex
import lexer
import error
import ast_


def parse_global(tokens: list[Token], text: str) -> list[ast_.Func | ast_.Import | ast_.ImportFrom]:
    _l_t: Token | None = None

    def expect(data: str | None = None, type_: str | None = None) -> Token:
        nonlocal tokens, text, _l_t

        if data is None and type_ is None:
            raise ValueError('expect(None, None)')

        t: Token
        try:
            t = tokens.pop(0)
        except IndexError:
            if _l_t is None:
                print(error.ANSI_ERROR + 'ERROR: unexpected EOF')
                exit(1)
            if data is not None:
                error.error([_l_t], 0, text, f"expected '{data}'", _exit=False)
                if type_ is not None:
                    error.note([_l_t], 0, text, False, ' ', f"of type '{type_}'")
                exit(1)
            elif type_ is not None:
                error.error([_l_t], 0, text, f"expected token of type '{type_}'")
            else:
                assert False

        t # noqa

        if data is not None:
            if t.data != data:
                tokens.insert(0, t)
                error.error_w_note(
                    tokens, 0, text,
                    "unexpected token",
                    True, data, 'should be this'
                )
        if type_ is not None:
            if t.type != type_:
                tokens.insert(0, t)
                error.error_w_note(tokens, 0, text, f"expected type '{type_}'",
                                   True, ' ', f"type '{type_}'")

        _l_t = t
        return t

    def accept(data: str | None = None, type_: str | None = None, inc: bool = True) -> bool:
        nonlocal tokens, text, _l_t

        if data is None and type_ is None:
            raise ValueError('expect(None, None)')

        if not tokens:
            if _l_t is None:
                print(error.ANSI_ERROR + 'ERROR: unexpected EOF')
                exit(1)
            if data is not None:
                error.error([_l_t], 0, text, f"expected '{data}'", _exit=False)
                if type_ is not None:
                    error.note([_l_t], 0, text, False, ' ', f"of type '{type_}'")
                exit(1)
            elif type_ is not None:
                error.error([_l_t], 0, text, f"expected token of type '{type_}'")
            else:
                assert False

        if data is not None:
            if tokens[0].data != data:
                return False
        if type_ is not None:
            if tokens[0].type != type_:
                return False

        if inc:
            _l_t = tokens.pop(0)
        return True

    def func_head(scope: ast_.Scope | None) -> ast_.Func:
        if scope is None:
            scope = ast_.Scope.PRIVATE  # TODO: allow implicit private?

        expect('func', 'STATEMENT')

        if accept(type_='NAME', inc=False):
            type_ = ast_.Type([])
            expect(type_='NAME')
        else:
            type_ = parse_type()
        name = expect(type_='NAME')
        if accept('{', 'TOKEN', inc=False):
            args = ast_.FuncArgs([])
        else:
            expect('(', 'TOKEN')
            args = ast_.FuncArgs([])

            while not accept(')', 'TOKEN'):
                raise NotImplementedError('function definition arguments')

        return ast_.Func(scope, type_, args, None)

    def parse_func_body() -> ast_.Block:
        block_type = ast_.BlockType.NORMAL
        if accept(data='#'):
            block_type = ast_.BlockType.GLOBAL
        elif accept(data='.'):
            block_type = ast_.BlockType.PARENT
        expect('{', 'TOKEN')

        out = []
        while not accept('}', 'TOKEN'):
            out.append(parse_expr())
            expect(';', 'TOKEN')

        return ast_.Block(block_type, out)

    def parse_expr() -> ast_.Expression:
        # /home/huub/Desktop/mds operator precedence.txt
        _ = {
            1: ['@'],
            2: [':='],
            3: ['^^'],
            4: ['||'],
            5: ['&&'],
            6: ['!'],
            7: ['in', '<', '<=', '>', '>=', '!=', '=='],
            8: ['|'],
            9: ['^'],
            10: ['&'],
            11: ['<<', '>>'],
            12: ['+', '-'],
            13: ['*', '/', '\\', '%', '%%'],
            14: ['-x', '~'],
            15: ['**']
        }
        _right = set('**')

        def _op(ops: list[tuple[str, ast_.OperationType]], next_: Callable[[], ast_.Expression]) -> ast_.Expression:
            lhs = next_()
            while True:
                op: ast_.OperationType | None = None
                for o in ops:
                    if accept(data=o[0]):
                        op = o[1]

                        if op is None:
                            raise ValueError
                        break

                if op is not None:
                    rhs = next_()
                    lhs = ast_.Operation(lhs, rhs, op)
                else:
                    return lhs

        def parse_pipe() -> ast_.Expression:
            return _op([('@', ast_.OperationType.PIPE)], parse_assign_expr)
        parse_first = parse_pipe

        def parse_assign_expr() -> ast_.Expression:
            return _op([(':=', ast_.OperationType.ASSIGN)], parse_logical_xor)

        def parse_logical_xor() -> ast_.Expression:
            return _op([('^^', ast_.OperationType.LOGICAL_XOR)], parse_logical_or)

        def parse_logical_or() -> ast_.Expression:
            return _op([('||', ast_.OperationType.LOGICAL_OR)], parse_logical_and)

        def parse_logical_and() -> ast_.Expression:
            return _op([('&&', ast_.OperationType.LOGICAL_AND)], parse_logical_not)

        def parse_logical_not() -> ast_.Expression:
            return _op([('|', ast_.OperationType.LOGICAL_NOT)], parse_comp)

        def parse_comp() -> ast_.Expression:
            # TODO: make 'not in' a single token, also add all the other tokens
            return _op([
                ('in', ast_.OperationType.CONTAINS),
                # ('not in', ast_.OperationType.NOT_CONTAINS),
                ('<', ast_.OperationType.COMP_LT),
                ('<=', ast_.OperationType.COMP_LE),
                ('>', ast_.OperationType.COMP_GT),
                ('>=', ast_.OperationType.COMP_GE),
                ('!=', ast_.OperationType.COMP_NE),
                ('==', ast_.OperationType.COMP_EQ)
            ], parse_binary_or)

        def parse_binary_or() -> ast_.Expression:
            return _op([('|', ast_.OperationType.BINARY_OR)], parse_binary_xor)

        def parse_binary_xor() -> ast_.Expression:
            return _op([('^', ast_.OperationType.BINARY_XOR)], parse_binary_and)

        def parse_binary_and() -> ast_.Expression:
            return _op([('&', ast_.OperationType.BINARY_AND)], parse_bitshift)

        def parse_bitshift() -> ast_.Expression:
            return _op([
                ('<<', ast_.OperationType.BITSHIFT_LEFT),
                ('>>', ast_.OperationType.BITSHIFT_RIGHT)
            ], parse_addition)

        def parse_addition() -> ast_.Expression:
            return _op([
                ('+', ast_.OperationType.ADDITION),
                ('-', ast_.OperationType.SUBTRACTION)
            ], parse_multiplication)

        def parse_multiplication() -> ast_.Expression:
            return _op([  # '\\', '%', '%%'
                ('*', ast_.OperationType.MULTIPLICATION),
                ('/', ast_.OperationType.DIVISION),
                ('\\', ast_.OperationType.FLOOR_DIVISION),
                ('%', ast_.OperationType.MODULO),
                ('%%', ast_.OperationType.FLOOR_MODULO)
            ], parse_parenthesis)

        def parse_parenthesis() -> ast_.Expression:
            if accept(data='('):
                res = parse_first()
                expect(data=')')
                return res
            return parse_function()

        def parse_function() -> ast_.Expression:
            if accept(type_='NAME', inc=False):
                function_name = expect(type_='NAME').data

                expect(data='(')

                values = [parse_first()]
                while accept(data=','):
                    values.append(parse_first())

                expect(data=')')
                return ast_.FuncCall(function_name, values)
            return parse_unary()

        def parse_unary() -> ast_.Expression:
            if accept(data='-'):
                return ast_.UnaryOperation(parse_parenthesis(), ast_.UnaryOperationType.NEGATE)
            elif accept(data='~'):
                return ast_.UnaryOperation(parse_parenthesis(), ast_.UnaryOperationType.BINARY_NOT)
            else:
                return parse_exponent()

        def parse_exponent() -> ast_.Expression:
            return _op([('**', ast_.OperationType.EXPONENT)], parse_number)

        def parse_number() -> ast_.Expression:
            if accept(type_='STRING', inc=False):
                return ast_.StringLiteral(expect(type_='STR_LIT').data)
            elif accept(type_='INT_LIT', inc=False):
                return ast_.NumberLiteral(lexer.lex_number(expect(type_='INT_LIT').data))
            else:
                error.error(tokens, 0, text, '')

        return parse_first()

    def parse_type() -> ast_.Type:
        if accept('(', 'TOKEN'):
            raise NotImplementedError('tuples')
        else:
            return ast_.Type([ast_.SubType(expect(type_='NAME').data, [])])

    out = []

    while tokens:
        print(tokens)
        print(out)
        if accept('import', 'STATEMENT'):
            raise NotImplementedError
        # TODO: abstract 'private' and 'public' to list
        elif accept('private', 'STATEMENT', inc=False) or accept('public', 'STATEMENT', inc=False):
            if accept('private', 'STATEMENT'):
                scope = ast_.Scope.PRIVATE
            elif accept('public', 'STATEMENT'):
                scope = ast_.Scope.PUBLIC
            else:
                raise AssertionError

            if accept('func', 'STATEMENT', inc=False):
                out.append(func_head(scope))
                parse_func_body()
                continue
            else:  # a variable
                type_ = parse_type()
            raise NotImplementedError('function and variable scopes')
        elif accept('func', 'STATEMENT', inc=False):
            out.append(func_head(None))
            out[-1].body = parse_func_body()
        elif accept('from', 'STATEMENT'):
            module = expect(type_='NAME')
            expect('import', 'STATEMENT')
            item = expect(type_='NAME')

            if accept(';', 'TOKEN'):
                as_ = None
            else:
                as_ = expect(type_='NAME')

            out.append(ast_.ImportFrom(module.data, item.data, as_))
        else:
            error.error(tokens, 0, text, f"unexpected token")

    return out


if __name__ == '__main__':
    def test(text: str, eq) -> None:
        l = parse_global(lex(text), text)
        r = eq
        assert l == r, f'{l} != {r}'

    test('func void foo() {}', [ast_.Func(scope=ast_.Scope.PRIVATE, return_type=ast_.Type(type=[]), args=ast_.FuncArgs(args=[]), body=None)])
    test('func void foo () {print(1 + 2);}', 0)
