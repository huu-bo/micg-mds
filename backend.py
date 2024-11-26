import typing

import ast_
import error
import il
import types_

# Force these functions to be global in the assembly, even if they are marked as private
#  TODO: Should the functions be forced to be PRIVATE in the mds code?
force_global = {
    'main'
}
RUNTIME_FUNCS = {
    'mds_alloc_stack_var'
}
OPERATION_NAME: dict[ast_.OperationType, str] = {
    ast_.OperationType.ADDITION: 'add',
    ast_.OperationType.MULTIPLICATION: 'mul'
}


def ir_to_asm(ir: list[il.Op], file: typing.TextIO) -> None:
    """Outputs nasm x86_64 to file"""

    file.write('; prelude\n')
    file.write('[BITS 64]\n')
    file.write('section .text\n')

    file.write('; Runtime functions\n')
    for func in RUNTIME_FUNCS:
        file.write(f'    extern {func}\n')

    file.write('; code\n')
    func_vars: dict[str, int] = {}

    def next_var_index() -> int:
        if func_vars:
            return max(func_vars.values()) + 1
        else:
            return 1

    for op in ir:
        file.write(f'  ; op: {op}\n')
        if isinstance(op, il.FuncDef):
            func_name = op.metadata.func_name
            if op.metadata.scope == ast_.Scope.PUBLIC or func_name in force_global:
                file.write(f'global {func_name}\n')
            file.write(f'{func_name}:\n')

            file.write(f'    push rbp\n')
            file.write(f'    mov rbp, rsp\n')

        elif isinstance(op, il.FuncCall):
            # TODO: things with rbp or smth
            file.write(f'    call {op.func_name}\n')

        elif isinstance(op, il.Drop):
            file.write('    pop rax\n')

        elif isinstance(op, il.ImmediateValue):
            if op.value.type.type == types_.Types.INT:
                file.write(f'    push DWORD {op.value.value}\n')
            elif op.value.type.type == types_.Types.VOID:
                file.write('    sub rsp, 8')

            else:
                raise NotImplementedError(f'ImmediateValue {op.value}')

        elif isinstance(op, il.VarAssignment):
            if op.var_name not in func_vars:
                var_index = next_var_index()
                func_vars[op.var_name] = var_index

                file.write(f'    mov rsi, {var_index}\n')
                file.write('    call mds_alloc_stack_var\n')

            file.write(f'    mov rax, [rsp - 8]\n')
            file.write(f'    mov [rbp - {func_vars[op.var_name] * 8}], rax\n')

        elif isinstance(op, il.GetFromFuncScope):
            if op.var_name not in func_vars:
                print(error.ANSI_ERROR + f'ERROR: variable {repr(op.var_name)} not defined')
                exit(1)
            file.write(f'    mov rax, [rbp - {func_vars[op.var_name] * 8}]\n')
            file.write(f'    push rax\n')

        elif isinstance(op, il.Operation):
            # TODO: this could be a string operation
            file.write('    pop rbx\n')
            file.write('    pop rax\n')
            file.write(f'    {OPERATION_NAME[op.op_type]} rax, rbx\n')
            file.write('    push rax\n')

        elif isinstance(op, il.Return):
            file.write('    pop rax\n')  # return value
            file.write(f'    add rsp, {next_var_index() * 8}')
            file.write('    pop rbp\n')
            file.write('    ret\n')

        else:
            raise NotImplementedError(f'ir_to_asm {type(op)}, {op}')
