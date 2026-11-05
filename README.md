# ARCompact for Ghidra

Standalone, experimental **ARCv1 / ARCompact** processor extension, derived from
[niooss-ledger/ghidra](https://github.com/niooss-ledger/ghidra/tree/d3fbf109ada6d051750e973779170c1758622530/Ghidra/Processors/ARC).
This is not ARCv2, an authoritative MEC1653 hardware model, or a claim of complete
instruction/interrupt ABI coverage. Tested with **Ghidra 12.1.2, JDK 21, Linux**;
other releases/platforms are unvalidated.

## Changes in this extraction

- Compose live STATUS32 Z/N/C/V flags when reading the auxiliary status register.
- Recover conditional hardware-loop backedges without changing architectural
  LP_START/LP_END on a false condition. An analysis-only start shadow is explicit
  and synchronized on writes to LP_START.
- Correct the observed GNU ARCompact 8-byte scalar alignment to 4 and include r24
  in the preserved register set.
- Provide an **opt-in** `__arc_status_leaf` calling convention for proven helpers
  preserving non-result GPRs. Do not apply it to arbitrary functions.
- Provide manually selectable `arcompact_*` millicode callfixups. No names or
  addresses automatically enable them. They model a specific GPR push/restore
  family: the **caller saves blink**, push helpers save GPRs only, and restore
  tails recover the caller's blink word. Check assembly and stack deltas first.
- Include original synthetic STATUS32/LP execution and recovered-C regressions.

The SLEIGH changes are based on demonstrated mismatches, not simply on whether
a large firmware corpus decompiles. Residual indirect-flow, IRQ-return and ABI
problems remain. Native AUX accesses and physical side effects are not emulated
by these decompiler fixes. Millicode model availability is not proof that every
save/restore variant has been independently executed.

## Build and install

Prerequisites: Python 3.11+, a complete Ghidra distribution and its supported JDK.
No network access or Gradle is needed by the build:

```sh
python3 build.py --ghidra-dir /path/to/ghidra --java-home /path/to/jdk21
# or export GHIDRA_INSTALL_DIR and JAVA_HOME, then python3 build.py
```

The ZIP is `dist/ghidra_<version>_ARCompact.zip`. In a **separate** Ghidra
installation/profile, use File → Install Extensions, select the ZIP and restart.
The language ID is `ARCompact:LE:32:default`. The `default` compiler spec models
the observed GNU ABI subset, not every proprietary vendor ABI.

Remove any other extension/module defining this language before installation;
duplicate ARC language definitions are unsupported. Never overwrite a working
installation or silently change an unrelated project's language/compiler spec.
The build writes only `build/` and `dist/`, uses an explicit JDK, and does not
modify your SDK or saved Ghidra launcher settings. No SDK binaries are committed.

## Tests

```sh
python3 -m unittest discover -s tests -v
python3 tests/check.py --ghidra-dir /path/to/ghidra --java-home /path/to/jdk21 \
  --arc-prefix /path/to/arc-elf32- --qemu /path/to/qemu-system-arc
```

The execution test requires GNU tools supporting `-mcpu=arc600`, a QEMU build
supporting the experimental ARC600 CPU, and a host C compiler (`CC`, default
`cc`). It uses only synthetic source, **no vendor firmware**. The reference
QEMU work is [here](https://github.com/ArthurHeymans/qemu/tree/arc600); standard
upstream QEMU support should not be assumed.

Tests install the actual ZIP into a disposable private SDK copy/project, execute word-aligned GNU probes
with poisoned inputs under QEMU, decompile them, require constant STATUS32
results and recovered hardware-loop flow, and compile/run only our small known
recovered-C fixture on the host. A wrong expectation must exit 42. Counts include
-1, 0, 1, 2, 7, 85 and false-condition
AUX-state preservation. Reports under `build/` record source/artifact hashes.
Completion, matching test cases and correct decoding of these probes are not a
full ISA, concurrency, thermal-safety or complete firmware-boot validation.

## Provenance and license

Apache-2.0 with the original MeP-derived data-organization MIT notice retained
in [third-party attribution](THIRD_PARTY.md). Upstream headers, `LICENSE`/`NOTICE`
and [author attribution](AUTHORS.md) are retained. `UPSTREAM.json` records the exact source revision and original file hashes. The internal
upstream Gradle build is replaced by a standalone packaging script; no Ghidra
SDK is bundled. Additional changes and test fixtures were developed during
ThinkPad T480 EC research, but this repository contains **no firmware, board
annotations, board-net claims, decompiler projects or extracted vendor data**.
