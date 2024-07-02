import parser
import types_
from lexer import lex

if __name__ == '__main__':
    with open('main.mds', 'r') as file:
        data = file.read()
    # data = 'print(a);'

    tokens = lex(data)
    tree = parser.parse_global(tokens, data)
    print(tree)
    types_.check_types(tree)
