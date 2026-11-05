# SPDX-License-Identifier: Apache-2.0
import importlib.util
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('extension_build', ROOT / 'build.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class PackageTests(unittest.TestCase):
    def test_abi(self):
        tree = ET.parse(ROOT / 'data/languages/ARCompact.cspec')
        self.assertEqual(tree.find('.//size_alignment_map/entry[@size="8"]').get('alignment'), '4')
        for prototype in tree.findall('.//prototype'):
            self.assertIn('r24', [r.get('name') for r in prototype.findall('./unaffected/register')])
        self.assertIsNotNone(tree.find('.//prototype[@name="__arc_status_leaf"]'))

    def test_opt_in_fixups(self):
        tree = ET.parse(ROOT / 'data/languages/ARCompact.cspec')
        fixups = tree.findall('.//callfixup')
        self.assertEqual(len(fixups), 28)
        self.assertTrue(all(f.get('name').startswith('arcompact_') for f in fixups))
        self.assertTrue(all(not f.findall('target') for f in fixups))
        for fixup in fixups:
            text = fixup.find('./pcode/body').text
            if 'push_' in fixup.get('name'):
                self.assertNotIn('blink', text)
            else:
                self.assertIn('blink =', text)
                self.assertIn('return [blink]', text)

    def test_archive_is_stable(self):
        with tempfile.TemporaryDirectory() as directory:
            a, b = Path(directory) / 'a.zip', Path(directory) / 'b.zip'
            build.archive(a, {'z': b'z', 'a': b'a'})
            build.archive(b, {'a': b'a', 'z': b'z'})
            self.assertEqual(a.read_bytes(), b.read_bytes())
            with zipfile.ZipFile(a) as archive:
                self.assertEqual(archive.namelist(), ['a', 'z'])

    def test_no_board_specific_bindings(self):
        for path in (ROOT / 'data').rglob('*'):
            if path.is_file():
                self.assertNotIn('t480_', path.read_text().lower())
        self.assertEqual(ET.parse(ROOT / 'data/languages/ARCompact.ldefs').find('language').get('id'),
                         'ARCompact:LE:32:default')


if __name__ == '__main__':
    unittest.main()
