/* Synthetic QEMU RAM layout, deliberately unrelated to the EC memory map. */
ENTRY(_start)
MEMORY { RAM (rwx) : ORIGIN = 0x80000000, LENGTH = 16M }
SECTIONS {
    .text : ALIGN(4) { KEEP(*(.text.start)) *(.text .text.*) } > RAM
    .rodata : ALIGN(4) { *(.rodata .rodata.*) } > RAM
    .data : ALIGN(4) { *(.data .data.*) *(.sdata .sdata.*) } > RAM
    .bss (NOLOAD) : ALIGN(4) { *(.bss .bss.*) *(.sbss .sbss.*) *(COMMON) } > RAM
    __stack_top = ORIGIN(RAM) + LENGTH(RAM) - 16;
    ASSERT(. < __stack_top - 0x10000, "test image overlaps stack")
}
