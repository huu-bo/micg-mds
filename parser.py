from __future__ import annotations

from lexer import Token, lex
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

    def next_(data: str | None = None, type_: str | None = None, inc: bool = True) -> bool:
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
        else:
            _l_t = None  # TODO: is this the correct behaviour?
        return True

    def func_head(scope: ast_.Scope | None) -> ast_.Func:
        if scope is None:
            scope = ast_.Scope.PRIVATE  # TODO: allow implicit private?

        expect('func', 'STATEMENT')

        if next_(type_='NAME', inc=False):
            type_ = ast_.Type([])
            expect(type_='NAME')
        else:
            type_ = parse_type()
        name = expect(type_='NAME')
        if next_('{', 'TOKEN', inc=False):
            args = ast_.FuncArgs([])
        else:
            expect('(', 'TOKEN')
            args = ast_.FuncArgs([])

            while not next_(')', 'TOKEN'):
                raise NotImplementedError('function definition arguments')

        return ast_.Func(scope, type_, args, None)

    def parse_func_body() -> list[ast_.Expression]:
        expect('{', 'TOKEN')

        out = []
        while not next_('}', 'TOKEN'):
            out.append(parse_expr())
            expect(';', 'TOKEN')

        return out

    def parse_expr() -> ast_.Expression:
        asso = {
            '+': [(2, 'left')],
            '-': [(2, 'left'), (5, 'unary')],
            '*': [(3, 'left')],
            '/': [(3, 'left')],
            '^': [(4, 'right')],
            '++': [(5, 'unary')],
            '--': [(5, 'unary')],
            'callfunc': 6
        }
        # /home/huub/Desktop/mds operator precedence.txt
        asso = {
            1: [':=', '@'],
            2: ['^^'],
            3: ['||'],
            4: ['&&'],
            5: ['!'],
            6: ['in', 'not in', '<', '<=', '>', '>=', '!=', '=='],
            7: ['|'],
            8: ['^'],
            9: ['&'],
            10: ['<<', '>>'],
            11: ['+', '-'],
            12: ['*', '/', '\\', '%', '%%'],
            13: ['-x', '~'],
            14: ['**']
        }
        min_asso = min(asso)
        max_asso = max(asso)
        right = {'**'}

        operator = []
        out: ast_.Expression | None = None
        while not next_(';', 'TOKEN', inc=False):
            if next_(type_='INT_LIT', inc=False):
                operator.append(expect(type_='INT_LIT'))
            elif next_('(', 'TOKEN', inc=False):
                operator.append(expect('(', 'TOKEN'))
            elif next_(')', 'TOKEN', inc=False):
                try:
                    while operator[-1] != ['TOKEN', '(']:
                        raise NotImplementedError
                except IndexError:
                    error.error_w_note(tokens, 0, text,
                                       "expected '('",
                                       True, ' ', "to open this ')'")

                expect(')', 'TOKEN')
                # TODO: function calls
            elif next_(type_='NAME', inc=False):
                operator.append(expect(type_='NAME'))
                operator.append('callfunc')

            else:
                try:
                    error.error(tokens, 0, text, 'unexpected')
                except IndexError:
                    print('unexpected EOF')
                    exit(1)

        print(out)

        raise NotImplementedError

    def parse_type() -> ast_.Type:
        if next_('(', 'TOKEN'):
            raise NotImplementedError('tuples')
        else:
            return ast_.Type([ast_.SubType(expect(type_='NAME').data, [])])

    out = []

    while tokens:
        print(tokens)
        print(out)
        if next_('import', 'STATEMENT'):
            raise NotImplementedError
        # TODO: abstract 'private' and 'public' to list
        elif next_('private', 'STATEMENT', inc=False) or next_('public', 'STATEMENT', inc=False):
            if next_('private', 'STATEMENT'):
                scope = ast_.Scope.PRIVATE
            elif next_('public', 'STATEMENT'):
                scope = ast_.Scope.PUBLIC
            else:
                raise AssertionError

            if next_('func', 'STATEMENT', inc=False):
                out.append(func_head(scope))
                parse_func_body()
                continue
            else:  # a variable
                type_ = parse_type()
            raise NotImplementedError('function and variable scopes')
        elif next_('func', 'STATEMENT', inc=False):
            out.append(func_head(None))
            parse_func_body()
        elif next_('from', 'STATEMENT'):
            module = expect(type_='NAME')
            expect('import', 'STATEMENT')
            item = expect(type_='NAME')

            if next_(';', 'TOKEN'):
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
    test('func void foo () {print(1 + 2)}', 0)
