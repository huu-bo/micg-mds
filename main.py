import subprocess

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
    temp_asm_path = 'temp.asm'
    with open(temp_asm_path, 'w') as file:
        backend.ir_to_asm(ir, file)

    temp_obj_path = 'temp.o'
    subprocess.run(['nasm', temp_asm_path, '-f', 'elf64', '-o', temp_obj_path], check=True)

    # nasm runtime.asm -f elf64 -o runtime.o
    # gcc std.c -ffreestanding -o std.o
    # ld runtime.o std.o -i -o lib.o  # TODO: what should the runtime + std object be called?
    runtime_obj_path = 'runtime.o'
    out_path = 'a.elf'
    subprocess.run(['ld', temp_obj_path, runtime_obj_path, '-o', out_path], check=True)
