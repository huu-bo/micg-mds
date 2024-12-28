[BITS 64]
section .text

; x86 stack grows downward 💀

%define STDOUT 1

%define SYSCALL_WRITE 0x01
%define SYSCALL_MMAP  0x09
%define SYSCALL_EXIT  0x3c

section .data
newline: db 0xA
section .text

global println
println:
    mov rax, [rdx]

.strlen_loop:
    inc rax
    cmp byte [rax], 0
    jne .strlen_loop

    mov rcx, rdx

    mov rdx, rax   ; length
    sub rdx, [rcx]

    mov rax, SYSCALL_WRITE
    mov rdi, STDOUT
    mov rsi, [rcx]
    ; rdx: length
    push rcx
    syscall

    mov rax, SYSCALL_WRITE
    mov rdi, STDOUT   ; fd
    mov rsi, newline  ; buf
    mov rdx, 1        ; length
    syscall  ; TODO: make this one syscall
    pop rcx

    mov rdx, rcx
    ret

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
