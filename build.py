#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build an ARCompact extension using an installed Ghidra SDK and JDK (no Gradle)."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parent


def run(command, **kwargs):
    print('+', ' '.join(map(str, command)), flush=True)
    subprocess.run(list(map(str, command)), check=True, **kwargs)


def java_command(sdk, java, settings, main):
    settings.mkdir(parents=True, exist_ok=True)
    return [java / 'bin/java', '-Xmx1G', '-Djava.awt.headless=true',
            '-Duser.home=' + str(settings),
            '-Djava.system.class.loader=ghidra.GhidraClassLoader', '-cp',
            sdk / 'Ghidra/Framework/Utility/lib/Utility.jar', 'ghidra.Ghidra', main]


def java_environment(java, settings):
    return dict(os.environ, JAVA_HOME=str(java), HOME=str(settings),
                XDG_CONFIG_HOME=str(settings / 'config'), XDG_CACHE_HOME=str(settings / 'cache'))


def archive(destination, files):
    """Stable ordering/timestamps/modes; no SDK, firmware or absolute paths."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED) as out:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            out.writestr(info, data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ghidra-dir', type=Path, default=os.getenv('GHIDRA_INSTALL_DIR'))
    parser.add_argument('--java-home', type=Path, default=os.getenv('JAVA_HOME'))
    args = parser.parse_args()
    if not args.ghidra_dir or not args.java_home:
        parser.error('supply --ghidra-dir/GHIDRA_INSTALL_DIR and --java-home/JAVA_HOME')
    sdk, java = args.ghidra_dir.resolve(strict=True), args.java_home.resolve(strict=True)
    properties = dict(line.split('=', 1) for line in (sdk / 'Ghidra/application.properties').read_text().splitlines()
                      if '=' in line and not line.startswith('#'))
    version = properties['application.version'].strip()
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', version):
        raise ValueError('unsafe SDK version')
    stage, classes = ROOT / 'build/extension/ARCompact', ROOT / 'build/classes'
    for directory in (stage, classes):
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True)
    shutil.copytree(ROOT / 'data', stage / 'data')
    shutil.copytree(ROOT / 'licenses', stage / 'licenses')
    for name in ('Module.manifest', 'LICENSE', 'NOTICE', 'UPSTREAM.json', 'AUTHORS.md', 'THIRD_PARTY.md', 'README.md'):
        shutil.copy2(ROOT / name, stage / name)
    (stage / 'extension.properties').write_text((ROOT / 'extension.properties').read_text().replace('@GHIDRA_VERSION@', version))
    languages = stage / 'data/languages'
    run(java_command(sdk, java, ROOT / 'build/settings',
                     'ghidra.pcodeCPort.slgh_compile.SleighCompileLauncher') +
        [languages / 'ARCompact.slaspec', languages / 'ARCompact.sla'],
        env=java_environment(java, ROOT / 'build/settings'))
    sources = sorted((ROOT / 'src/main/java').rglob('*.java'))
    classpath = os.pathsep.join(map(str, sorted(sdk.glob('Ghidra/**/lib/*.jar'))))
    run([java / 'bin/javac', '--release', '21', '-encoding', 'UTF-8', '-cp', classpath,
         '-d', classes, *sources])
    archive(stage / 'lib/ARCompact.jar', {str(p.relative_to(classes)): p.read_bytes()
                                       for p in classes.rglob('*.class')})
    files = {str(p.relative_to(stage.parent)): p.read_bytes() for p in stage.rglob('*') if p.is_file()}
    output = ROOT / f'dist/ghidra_{version}_ARCompact.zip'
    archive(output, files)
    source_files = [ROOT / 'build.py', ROOT / 'extension.properties', ROOT / 'UPSTREAM.json',
                    *sorted((ROOT / 'data').rglob('*')), *sources]
    record = {'ghidra_version': version, 'sdk': str(sdk), 'java_home': str(java),
              'archive': str(output), 'archive_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
              'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in source_files if p.is_file()}}
    (ROOT / 'build/build.json').write_text(json.dumps(record, indent=2) + '\n')
    print(output)


if __name__ == '__main__':
    main()
