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
    'mds_cast_int_to_string',
    
    'println',  # TODO: This is a hack, implement import statements
    'print'
}
OPERATION_NAME: dict[ast_.OperationType, str] = {
    ast_.OperationType.ADDITION: 'add',
}

INT64_STR_MAX_SIZE = 20  # floor(log10(2<<64)+1)


def ir_to_asm(ir: list[il.Op], file: typing.TextIO) -> None:
    """Outputs nasm x86_64 to file"""

    # Registers:
    #    rax, rbx, rcx: scratch
    #    rdx: data stack

    file.write('; prelude\n')
    file.write('[BITS 64]\n')
    file.write('section .text\n')

    file.write('; Runtime functions\n')
    for func in RUNTIME_FUNCS:
        file.write(f'    extern {func}\n')

    file.write('; code\n')
    func_vars: dict[str, int] = {}

    def next_var_index(size: int = 1) -> int:
        if func_vars:
            return max(func_vars.values()) + size
        else:
            return 1

    const_index = 0

    def next_const_index() -> int:
        nonlocal const_index
        c = const_index
        const_index += 1
        return c

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
            if op.return_type.type == types_.Types.STRING:
                raise NotImplementedError('Copying string to stack')

        elif isinstance(op, il.Drop):
            # file.write('    pop rax\n')
            file.write('    add rdx, 8\n')

        elif isinstance(op, il.ImmediateValue):
            if op.value.type.type == types_.Types.INT:
                file.write('    sub rdx, 8\n')
                file.write(f'    mov rax, {op.value.value}\n')
                file.write('    mov qword [rdx], rax\n')
            elif op.value.type.type == types_.Types.VOID:
                file.write('    sub rdx, 8\n')

            elif op.value.type.type == types_.Types.STRING:
                file.write('section .data\n')
                c = next_const_index()
                encoded = [str(v) for v in op.value.value.encode('utf-8')] + ['0']
                length = len(encoded) | 7
                while len(encoded) < length:
                    encoded.append('0')
                temp_name = f'_const_{c}'
                file.write(f'    {temp_name}: db ' + ', '.join(encoded) + '\n')
                file.write('section .text\n')

                var_index = next_var_index(length)
                func_vars[temp_name] = var_index

                file.write('    cld\n')
                file.write(f'    mov rcx, {(length >> 3) + 1}\n')
                file.write(f'    mov rsi, _const_{c}\n')
                file.write(f'    lea rdi, [rbp - {var_index * 8}]\n')
                file.write('    rep movsq\n')
                file.write(f'    sub rsp, {length}\n')
                file.write('    sub rdx, 8\n')
                file.write(f'    lea rax, [rbp - {var_index * 8}]\n')
                file.write(f'    mov qword [rdx], rax\n')

            else:
                raise NotImplementedError(f'ImmediateValue {op.value}')

        elif isinstance(op, il.VarAssignment):
            if op.var_name not in func_vars:
                var_index = next_var_index()
                func_vars[op.var_name] = var_index

                # file.write(f'    mov rsi, {var_index}\n')
                # file.write('    call mds_alloc_stack_var\n')
                file.write('    sub rsp, 8\n')

            file.write(f'    mov rax, [rdx]\n')
            # variables are at [rbp - var_index * 8]
            file.write(f'    mov [rbp - {func_vars[op.var_name] * 8}], rax\n')

        elif isinstance(op, il.GetFromFuncScope):
            if op.var_name not in func_vars:
                print(error.ANSI_ERROR + f'ERROR: variable {repr(op.var_name)} not defined')
                exit(1)
            file.write(f'    mov rax, [rbp - {func_vars[op.var_name] * 8}]\n')
            file.write('    sub rdx, 8\n')
            file.write('    mov [rdx], rax\n')

        elif isinstance(op, il.Operation):
            if op.op_type == ast_.OperationType.CAST:
                if op.from_type.type == types_.Types.INT and op.to_type.type == types_.Types.STRING:
                    var_index = next_var_index(INT64_STR_MAX_SIZE)
                    func_vars[f'_const_{next_const_index()}'] = var_index

                    file.write(f'    lea rax, [rbp - {var_index * 8}]\n')
                    file.write('    sub rdx, 8\n')
                    file.write('    mov [rdx], rax\n')

                    file.write('    call mds_cast_int_to_string\n')

                    file.write(f'    lea rax, [rbp - {var_index * 8}]\n')
                    file.write('    sub rdx, 8\n')
                    file.write('    mov [rdx], rax\n')
                else:
                    raise NotImplementedError(f'OperationType cast (from {op.from_type} to {op.to_type})')
            else:
                # TODO: this could be a string operation
                file.write('    mov rbx, [rdx]\n')
                file.write('    mov rax, [rdx + 8]\n')
                file.write('    add rdx, 8\n')
                if op.op_type == ast_.OperationType.MULTIPLICATION:
                    file.write('    mov rcx, rdx\n')
                    file.write('    mul rbx\n')
                    # TODO: Check OF (overflows to rdx)
                    #           https://www.felixcloutier.com/x86/mul
                    file.write('    mov rdx, rcx\n')
                else:
                    file.write(f'    {OPERATION_NAME[op.op_type]} rax, rbx\n')
                file.write('    mov [rdx], rax\n')

        elif isinstance(op, il.UnaryOperation):
            if op.op_type == ast_.UnaryOperationType.NEGATE:
                file.write('    neg qword [rdx]\n')

            else:
                raise NotImplementedError(f'UnaryOperationType {op.op_type}')

        elif isinstance(op, il.Return):
            file.write('    mov rax, [rdx]\n')  # return value
            file.write('    add rdx, 8\n')
            # file.write(f'    add rsp, {(next_var_index() - 1) * 8}\n')
            # file.write('    pop rbp\n')
            file.write('    leave\n')
            file.write('    ret\n')

        else:
            raise NotImplementedError(f'ir_to_asm {type(op)}, {op}')
