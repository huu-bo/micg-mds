[BITS 64]
section .text

; x86 stack grows downward 💀

global mds_alloc_stack_var
; args: rsi var_index
mds_alloc_stack_var:
    mov rax, rsp
.op_stack_loop:
    add rax, 8

    mov rbx, [rax]
    mov [rax-8], rbx

    cmp rax, rbp
    jne .op_stack_loop

    sub rsp, 8

    mov rax, rsi
.var_stack_loop:
    dec rax
    jz .var_stack_loop_end

    inc rax
    mov rbx, [rbp + rax*8]
    dec rax
    mov [rbp + rax*8], rbx

    jmp .var_stack_loop

.var_stack_loop_end:

    sub rbp, 8
    ret
