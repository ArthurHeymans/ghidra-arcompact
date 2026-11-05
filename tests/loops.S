/* Small hardware-loop probes, independent of proprietary firmware. */
.text
.balign 4
.global probe_lp_signed
.type probe_lp_signed,@function
probe_lp_signed:
    mov r1,0
    cmp r0,0
    mov.gt lp_count,r0
    lpgt .Lsigned_end
    add r1,r1,1
.Lsigned_end:
    mov r0,r1
    j_s [blink]
.size probe_lp_signed,.-probe_lp_signed

.balign 4
.global probe_lp_false_preserves_aux
.type probe_lp_false_preserves_aux,@function
probe_lp_false_preserves_aux:
    mov r2,0x1234
    sr r2,[2]
    sr r2,[3]
    mov r0,0
    cmp r0,0
    mov.gt lp_count,r0
    lpgt .Lfalse_end
    mov r2,42
.Lfalse_end:
    lr r0,[2]
    j_s [blink]
.size probe_lp_false_preserves_aux,.-probe_lp_false_preserves_aux
