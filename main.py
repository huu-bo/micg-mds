import parser
import types_
from lexer import lex
import backend

if __name__ == '__main__':
    with open('main.mds', 'r') as file:
        data = file.read()
    # data = 'print(a);'

    tokens = lex(data)
    tree = parser.parse_global(tokens, data)
    print(tree)
    ir = types_.check_types(tree)
    print(ir)
    with open('temp.asm', 'w') as file:
        backend.ir_to_asm(ir, file)
