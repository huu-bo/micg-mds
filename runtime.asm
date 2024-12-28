[BITS 64]
section .text

; x86 stack grows downward 💀

global mds_alloc_stack_var
; args: rsi var_index
mds_alloc_stack_var:
    ; mov rax, rsp
    lea rax, [rsp-8]
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

; extern _println_implementation
; global println
; println:

%define SYSCALL_MMAP 0x09
%define SYSCALL_EXIT 0x3c

%define MAP_PRIVATE   0x0002
%define MAP_GROWSDOWN 0x0100
%define MAP_ANONYMOUS 0x0020

%define PROT_READ  0x1
%define PROT_WRITE 0x2

extern main
global _start
_start:
    mov rax, SYSCALL_MMAP
    mov rdi, 0     ; addr
    mov rsi, 4096  ; len
    mov rdx, PROT_READ | PROT_WRITE  ; prot
    mov r10, MAP_PRIVATE | MAP_GROWSDOWN | MAP_ANONYMOUS  ; flags
    mov r8, -1     ; fd
    mov r9, 0      ; offset
    syscall

    cmp rax, -1
    je .stack_alloc_fail
    mov rdx, rax

    call main

    mov rax, SYSCALL_EXIT
    mov rdi, 0
    syscall

.stack_alloc_fail:
    mov rax, SYSCALL_EXIT
    mov rdi, 1  ; TODO: An error code which denotes mds runtime failure as opposed to program failure
    syscall
