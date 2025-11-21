import argparse
import contextlib
import enum
import os
import subprocess
import sys
import tempfile
import typing

import parser
import types_
from lexer import lex
import backend


def _compile(source_file_path: typing.Union[str, None], runtime_object_path: str, temp_asm_path: str = 'temp.asm', temp_object_path: typing.Union[str, None] = 'temp.o', out_path: typing.Union[str, None] = 'a.elf', debug_log: bool = False) -> None:
    if source_file_path is None:
        if debug_log:
            print('Reading input from stdin')
        data = sys.stdin.read()
    else:
        if debug_log:
            print(f'Reading input from file {source_file_path}')
        with open(source_file_path, 'r') as file:
            data = file.read()

    tokens = lex(data)
    if debug_log:
        print('tokens:', tokens)
    tree = parser.parse_global(tokens, data)
    if debug_log:
        print('tree:', tree)
    ir = types_.check_types(tree)
    if debug_log:
        print('ir:', ir)

    if debug_log:
        print(f'Outputting assembly to {temp_asm_path}')
    with open(temp_asm_path, 'w') as file:
        backend.ir_to_asm(ir, file)

    if temp_object_path is None:
        return
    asm_args = ['nasm', temp_asm_path, '-f', 'elf64', '-o', temp_object_path]
    print('Assembling:', asm_args)
    subprocess.run(asm_args, check=True)

    if out_path is None:
        return
    ld_args = ['ld', temp_object_path, runtime_object_path, '-o', out_path]
    print('Linking:', ld_args)
    subprocess.run(ld_args, check=True)


if __name__ == '__main__':
    # with open('main.mds', 'r') as file:
    #     data = file.read()

    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument('input_filename')
    argument_parser.add_argument('-o', help='Output file, defaults to a.elf', const=None)
    argument_parser.add_argument('-s', action='store_true', help='Output assembly file')
    argument_parser.add_argument('-c', action='store_true', help='Output object file')

    # TODO: argument that makes the assembly_path=temp.asm, object_path=temp.o instead of tempfile.NamedTemporaryFile

    args = argument_parser.parse_args()
    print(args)


    class CompilationLevel(enum.StrEnum):
        ASSEMBLY = enum.auto()
        OBJECT = enum.auto()
        PROGRAM = enum.auto()


    in_filename: str = args.input_filename
    out_filename: typing.Union[str, None] = args.o
    if args.s:
        compilation_level = CompilationLevel.ASSEMBLY
        if args.c:
            print('WARNING: -s and -c specified, ignoring -c')
        if out_filename is None:
            out_filename, _ = os.path.splitext(in_filename)
            out_filename += '.asm'
    elif args.c:
        compilation_level = CompilationLevel.OBJECT
        if out_filename is None:
            out_filename, _ = os.path.splitext(in_filename)
            out_filename += '.o'
    else:
        compilation_level = CompilationLevel.PROGRAM

    runtime_object_path = 'runtime.o'


    @contextlib.contextmanager
    def named_temporary_file():
        with tempfile.NamedTemporaryFile() as file:
            yield file.name


    asm_path: typing.ContextManager
    if compilation_level == CompilationLevel.ASSEMBLY:
        asm_path = contextlib.nullcontext(out_filename)
    else:
        asm_path = named_temporary_file()

    object_path: typing.ContextManager
    if compilation_level == CompilationLevel.OBJECT:
        object_path = contextlib.nullcontext(out_filename)
    elif compilation_level == CompilationLevel.ASSEMBLY:
        object_path = contextlib.nullcontext()
    else:
        object_path = named_temporary_file()

    program_path: typing.ContextManager
    if compilation_level == CompilationLevel.PROGRAM:
        program_path = contextlib.nullcontext(out_filename)
    elif compilation_level == CompilationLevel.ASSEMBLY or compilation_level == CompilationLevel.OBJECT:
        program_path = contextlib.nullcontext()
    else:
        program_path = named_temporary_file()

    with asm_path as asm_path, object_path as object_path, program_path as program_path:
        _compile(
            in_filename if in_filename != '-' else None,
            runtime_object_path,
            temp_asm_path=asm_path,
            temp_object_path=object_path,
            out_path=program_path,
            debug_log=True
        )

    # nasm runtime.asm -f elf64 -o runtime.o
    # gcc std.c -ffreestanding -o std.o
    # ld runtime.o std.o -i -o lib.o  # TODO: what should the runtime + std object be called?
