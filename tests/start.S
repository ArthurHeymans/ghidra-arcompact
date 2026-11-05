/* QEMU-only entry/exit. This is not an MEC1653 reset vector or ISR. */
.section .text.start,"ax",@progbits
.balign 4
.global _start
.type _start,@function
_start:
    mov sp, __stack_top
    bl test_main
    /* ARC semihosting: SYS_exit = 1 in r8, status in r0, triggered by swi. */
    mov r8, 1
    swi
1:  b 1b
.size _start, .-_start

.global test_abort
.global abort
.type test_abort,@function
.type abort,@function
abort:
test_abort:
    mov r0, 90
    mov r8, 1
    swi
2:  b 2b
.size test_abort, .-test_abort
