/* SPDX-License-Identifier: Apache-2.0 */
#include <stdint.h>
extern uint32_t probe_status_z(uint32_t poison);
extern uint32_t probe_status_n(uint32_t poison);
extern uint32_t probe_status_c(uint32_t poison);
extern uint32_t probe_status_v(uint32_t poison);
extern uint32_t probe_lp_signed(int32_t count);
extern uint32_t probe_lp_false_preserves_aux(uint32_t poison);
uint32_t test_main(void) {
#ifdef NEGATIVE_CONTROL
    if (probe_status_z(0xdead1234) != 2) return 42;
#endif
    /* Poison r0 at each call: an accidentally misdirected return cannot pass. */
    if (probe_status_z(0xdead1234) != 1 || probe_status_n(0xdead1234) != 1 ||
        probe_status_c(0xdead1234) != 1 || probe_status_v(0xdead1234) != 1) return 42;
    if (probe_lp_signed(-1) != 0 || probe_lp_signed(0) != 0 ||
        probe_lp_signed(1) != 1 || probe_lp_signed(2) != 2 ||
        probe_lp_signed(7) != 7 || probe_lp_signed(85) != 85) return 43;
    if (probe_lp_false_preserves_aux(0xdead1234) != 0x1234) return 44;
    return 0;
}
