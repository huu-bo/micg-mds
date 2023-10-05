from typing import Union, Tuple, List
from parser import Token, parse

ANSI_ERROR = '\33[31m'
ANSI_WHITE = '\33[0m'
ANSI_NOTE = '\33[96'
ANSI_LINE = '\33[36m'


def error(tokens: List[Token], i: int, text: str, msg: str, _exit=True):
    print(f'{ANSI_ERROR}{tokens[i:i+7]}{ANSI_WHITE}')

    start_line_index, end_line_index = _get_line_i(tokens[i], text)
    print(text[start_line_index:end_line_index])

    if _exit:
        exit(1)


def _get_line_i(token: Token, text: str) -> Tuple[int, int]:
    start = token.index
    while text[start] != '\n' and start > 0:
        start -= 1
    if start > 0:
        start += 1

    end = token.index
    while end < len(text) and text[end] != '\n':
        end += 1

    return start, end


def _print_line_with_arrow_from_string(token: Token, text: str, color: str = ANSI_ERROR):
    print(ANSI_LINE, end='')
    print(str(token.line).rjust(4) + ' | ', end='')
    print(ANSI_WHITE, end='')

    start_line_i, end_line_i = _get_line_i(token, text)
    column = start_line_i + token.column

    length = len(token.data)
    print(text[start_line_i:column]
          + color
          + text[column:column + length]
          + ANSI_WHITE
          + text[column + length:end_line_i])
    print(' ' * (7 + column) + '^' + '~' * (length - 1))
    print(start_line_i, end_line_i, column, length, token.data)


if __name__ == '__main__':
    text = '''print ( ;
    test(tester, tester2);'''
    tokens = parse(text)

    print(tokens)

    LINE = '-' * 40

    error(tokens, 0, text, 'Test message.', _exit=False)
    print(LINE)
    error(tokens, 5, text, 'Test message.', _exit=False)
    print(LINE)
    for i in range(10):
        _print_line_with_arrow_from_string(tokens[i], text)
    print(LINE)
    print(list([token.line, token.column] for token in tokens))
    print(_get_line_i(tokens[0], text))
