/* Known-value probes for LR STATUS32's condition flags, not MEC hardware code. */
.text
.balign 4
.global probe_status_z
.type probe_status_z,@function
probe_status_z:
    mov r0,0
    cmp r0,r0
    lr r0,[0xa]
    lsr r0,r0,11
    bmsk r0,r0,0
    j_s [blink]
.size probe_status_z,.-probe_status_z

.balign 4
.global probe_status_n
.type probe_status_n,@function
probe_status_n:
    mov r0,0
    cmp r0,1
    lr r0,[0xa]
    lsr r0,r0,10
    bmsk r0,r0,0
    j_s [blink]
.size probe_status_n,.-probe_status_n

.balign 4
.global probe_status_c
.type probe_status_c,@function
probe_status_c:
    mov r0,-1
    add.f r0,r0,1
    lr r0,[0xa]
    lsr r0,r0,9
    bmsk r0,r0,0
    j_s [blink]
.size probe_status_c,.-probe_status_c

.balign 4
.global probe_status_v
.type probe_status_v,@function
probe_status_v:
    mov r0,0x7fffffff
    add.f r0,r0,1
    lr r0,[0xa]
    lsr r0,r0,8
    bmsk r0,r0,0
    j_s [blink]
.size probe_status_v,.-probe_status_v
