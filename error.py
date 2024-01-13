from typing import Union, Tuple, List
from lexer import Token, lex

ANSI_ERROR = '\33[31m'
ANSI_WHITE = '\33[0m'
ANSI_NOTE = '\33[96m'
ANSI_LINE = '\33[36m'


def error(tokens: List[Token], i: int, text: str, msg: str, _exit=True):
    print(f'{ANSI_ERROR}{tokens[i:i+7]}{ANSI_WHITE}')

    _print_line_with_arrow(tokens[i], text)

    print(f'{ANSI_ERROR}ERROR: {msg}{ANSI_WHITE}')

    if _exit:
        exit(1)


def error_w_note(tokens: List[Token], i: int, text: str, msg: str, note_replace: bool, note_replace_str: str, note_msg: str, _exit=True):
    print(f'{ANSI_ERROR}{tokens[i:i+7]}{ANSI_WHITE}')

    _print_line_with_arrow(tokens[i], text)
    print(f'{ANSI_ERROR}ERROR: {msg}{ANSI_WHITE}')

    note(tokens, i, text, note_replace, note_replace_str, note_msg)

    if _exit:
        exit(1)


def note(tokens: List[Token], i: int, text: str, replace: bool, replace_str: str, msg: str):
    _print_line_with_arrow_and_note(tokens[i], text, replace, replace_str)
    print(f'{ANSI_NOTE}NOTE: {msg}{ANSI_WHITE}')


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


def _print_line_with_arrow(token: Token, text: str, color: str = ANSI_ERROR):
    print(ANSI_LINE, end='')
    print(str(token.line).rjust(4) + ' | ', end='')
    print(ANSI_WHITE, end='')

    start_line_i, end_line_i = _get_line_i(token, text)
    column_index = start_line_i + token.column

    length = len(token.data)
    print(text[start_line_i:column_index]
          + color
          + text[column_index:column_index + length]
          + ANSI_WHITE
          + text[column_index + length:end_line_i])
    print(' ' * (7 + token.column) + '^' + '~' * (length - 1))


def _print_line_with_arrow_and_note(token: Token, text: str, replace: bool, replace_str: str, color: str = ANSI_NOTE):
    if replace:
        _print_line_with_arrow(token, text, color=color)
        print(color + ' ' * (7 + token.column) + replace_str + ANSI_WHITE)
    else:
        print(ANSI_LINE, end='')
        print(str(token.line).rjust(4) + ' | ', end='')
        print(ANSI_WHITE, end='')

        start_line_i, end_line_i = _get_line_i(token, text)
        column_index = start_line_i + token.column

        length = len(token.data)
        print(text[start_line_i:column_index + length]
              + color
              + replace_str
              + ANSI_WHITE
              + text[column_index + length:end_line_i])
        print(' ' * (7 + token.column + len(token.data)) + '^' + '~' * (len(replace_str) - 1))
        # TODO: this code is mostly duplicated


if __name__ == '__main__':
    text = '''print ( ;
    test(tester, tester2);'''
    tokens = lex(text)

    print(tokens)

    LINE = '-' * 40

    # error_w_note(tokens, 0, text, 'message', False, ';', 'note mesage')

    error(tokens, 0, text, 'Test message.', _exit=False)
    print(LINE)
    error(tokens, 5, text, 'Test message.', _exit=False)
    print(LINE)
    error_w_note(tokens, 2, text, 'Error message', True, ')', 'Note message', _exit=False)
    note(tokens, 2, text, True, 'var_name', 'It can be a variable.')
