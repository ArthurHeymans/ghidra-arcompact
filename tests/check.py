#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Independent GNU/QEMU, Ghidra decompilation, and recovered-C synthetic probes."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('extension_build', ROOT / 'build.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ghidra-dir', type=Path, required=True)
    parser.add_argument('--java-home', type=Path, required=True)
    parser.add_argument('--arc-prefix', required=True)
    parser.add_argument('--qemu', type=Path, required=True)
    args = parser.parse_args()
    sdk, java, qemu = (p.resolve(strict=True) for p in (args.ghidra_dir, args.java_home, args.qemu))
    output = ROOT / 'build/probes'
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    report = output / 'results.json'
    build.run([os.sys.executable, ROOT / 'build.py', '--ghidra-dir', sdk, '--java-home', java])
    gcc, nm = args.arc_prefix + 'gcc', args.arc_prefix + 'nm'
    image = output / 'synthetic.elf'
    compile_command = [gcc, '-mcpu=arc600', '-mbarrel-shifter', '-O2', '-ffreestanding', '-fno-builtin',
               '-nostdlib', '-nostartfiles', '-Wl,-T,' + str(ROOT / 'tests/qemu.ld'),
               *[ROOT / ('tests/' + p) for p in ('start.S', 'status32-probe.S', 'status32-driver.c', 'loops.S')],
               '-lgcc']
    build.run(compile_command + ['-o', image])
    symbols = subprocess.check_output([nm, '-n', image], text=True)
    for line in symbols.splitlines():
        fields = line.split()
        if len(fields) == 3 and fields[2].startswith('probe_') and int(fields[0], 16) % 4:
            raise RuntimeError('unaligned BL fixture: ' + line)
    qemu_command = [qemu, '-M', 'virt', '-cpu', 'arc600', '-m', '32M', '-nographic',
                    '-monitor', 'none', '-serial', 'none', '-semihosting', '-kernel']
    build.run(qemu_command + [image], timeout=10)
    negative = output / 'wrong-expectation.elf'
    build.run(compile_command + ['-DNEGATIVE_CONTROL', '-o', negative])
    result = subprocess.run(list(map(str, qemu_command + [negative])), timeout=10)
    if result.returncode != 42:
        raise RuntimeError('negative control did not exit42: ' + str(result.returncode))
    runtime = ROOT / 'build/test-runtime'
    record = ROOT / 'build/test-sdk.txt'
    if runtime.exists():
        if not record.exists() or record.read_text() != str(sdk):
            raise RuntimeError('refusing to mix SDKs in test runtime; remove build/test-runtime explicitly')
    else:
        shutil.copytree(sdk, runtime, symlinks=True)
        record.write_text(str(sdk))
    # The installation is disposable; the supplied SDK and global settings stay untouched.
    parent = runtime / 'Ghidra/Extensions'
    parent.parent.chmod(parent.parent.stat().st_mode | 0o200)
    parent.mkdir(exist_ok=True)
    parent.chmod(parent.stat().st_mode | 0o200)
    module = parent / 'ARCompact'
    if module.exists():
        shutil.rmtree(module)
    package = json.loads((ROOT / 'build/build.json').read_text())
    with zipfile.ZipFile(package['archive']) as archive:
        for name in archive.namelist():
            path = Path(name)
            if path.is_absolute() or '..' in path.parts or path.parts[0] != 'ARCompact':
                raise RuntimeError('unsafe extension archive member: ' + name)
            target = parent / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(name))
    projects = ROOT / 'build/test-projects'
    projects.mkdir(exist_ok=True)
    project = Path(tempfile.mkdtemp(prefix='synthetic-', dir=projects))
    command = build.java_command(runtime, java, ROOT / 'build/test-settings',
                                 'ghidra.app.util.headless.AnalyzeHeadless')
    build.run(command + [project, 'probes', '-import', image, '-processor', 'ARCompact:LE:32:default',
                         '-cspec', 'default', '-scriptPath', ROOT / 'tests',
                         '-postScript', 'CheckArcompactProbes.java', output, '-deleteProject', '-max-cpu', '2'],
              timeout=180, env=build.java_environment(java, ROOT / 'build/test-settings'))
    completed = json.loads((output / 'decompilation.json').read_text())
    if len(completed['passed']) != 6:
        raise RuntimeError('incomplete decompiler probes')
    recovered = output / 'recovered-loops.c'
    codes = [(output / (name + '.c')).read_text() for name in ('probe_lp_signed', 'probe_lp_false_preserves_aux')]
    recovered.write_text('''#include <stdint.h>
#include <stdbool.h>
typedef uint32_t uint, undefined4; typedef uint8_t byte;
uint Auxregs0008, Auxregs000c, _LP_START, _LP_END, _DAT_auxregs_0008, _DAT_auxregs_000c;
''' + '\n'.join(codes) + '''
int main(void) {
    int counts[] = {-1,0,1,2,7,85};
    for (unsigned i=0;i<6;i++) if (probe_lp_signed(counts[i]) != (counts[i]>0?counts[i]:0)) return 1;
    return probe_lp_false_preserves_aux() == 0x1234 ? 0 : 2;
}
''')
    host = output / 'recovered-loops'
    build.run([os.getenv('CC', 'cc'), '-std=gnu2x', '-O2', recovered, '-o', host])
    build.run([host], timeout=5)
    data = {'decompiler': completed, 'qemu': 'passed', 'negative_control_exit': 42, 'recovered_c': 'passed',
            'loop_counts': [-1, 0, 1, 2, 7, 85], 'false_condition_aux_preserved': True,
            'fixture_sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
            'build': json.loads((ROOT / 'build/build.json').read_text()),
            'scope': 'synthetic flags/conditional loops only; not complete ISA/IRQ/firmware validation'}
    report.write_text(json.dumps(data, indent=2) + '\n')
    print('Independent ARCompact synthetic regressions passed')


if __name__ == '__main__':
    main()
