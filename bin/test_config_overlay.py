#!/usr/bin/env python3
"""Regression test for partial config.d overlays (firmware issue #6102).

Run: python -m unittest bin/test_config_overlay.py
Set MESHTASTICD_BIN=/path/to/meshtasticd for the native integration test.
Without a built binary, the integration case is explicitly skipped.
"""
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


def emitted_value(output, section, key):
    """Read a top-level section's scalar from meshtasticd --output-yaml."""
    inside = False
    for line in output.splitlines():
        if re.fullmatch(r'[A-Za-z][A-Za-z0-9]*:', line):
            inside = line[:-1] == section
            continue
        if inside:
            # --output-yaml emits direct section children at two spaces.
            # A nested mapping may reuse a key, but is not the section value.
            match = re.fullmatch(r' {2}' + re.escape(key) + r':\s*(.*?)\s*', line)
            if match:
                return match.group(1).strip('"\'')
    raise AssertionError(f'Missing {section}.{key} in emitted YAML:\n{output}')


class ConfigOverlayTests(unittest.TestCase):
    def test_emitted_scalar_parser_is_section_scoped(self):
        output = 'General:\n  MaxNodes: 500\nLogging:\n  MaxNodes: 10\n'
        self.assertEqual(emitted_value(output, 'General', 'MaxNodes'), '500')
        self.assertEqual(emitted_value(output, 'Logging', 'MaxNodes'), '10')
        with self.assertRaises(AssertionError):
            emitted_value(output, 'HostMetrics', 'MaxNodes')

    def test_emitted_scalar_parser_ignores_nested_keys(self):
        output = (
            'General:\n'
            '  Nested:\n'
            '    MaxNodes: 999\n'
            '  MaxNodes: 500\n'
            'Logging:\n'
            '  MaxNodes: 10\n'
        )
        self.assertEqual(emitted_value(output, 'General', 'MaxNodes'), '500')
        self.assertEqual(emitted_value(output, 'Logging', 'MaxNodes'), '10')

    def test_emitted_scalar_parser_distinguishes_similar_section_names(self):
        output = (
            'GeneralExtra:\n'
            '  MaxNodes: 999\n'
            'General:\n'
            '  MaxNodes: 500\n'
            '  Nested:\n'
            '    MaxNodes: 888\n'
        )
        self.assertEqual(emitted_value(output, 'General', 'MaxNodes'), '500')
        self.assertEqual(emitted_value(output, 'GeneralExtra', 'MaxNodes'), '999')

    @unittest.skipUnless(os.environ.get('MESHTASTICD_BIN'),
                         'Set MESHTASTICD_BIN to run native overlay integration')
    def test_partial_overlays_preserve_unmentioned_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            overlay_dir = root / 'config.d'
            overlay_dir.mkdir()
            base = root / 'config.yaml'
            base.write_text(
                'General:\n'
                '  MaxNodes: 500\n'
                '  MaxMessageQueue: 100\n'
                f'  ConfigDirectory: {overlay_dir}/\n'
                '  MACAddress: "020000000001"\n'
                '  APIPort: 4403\n'
                'Logging:\n'
                '  LogLevel: debug\n'
                '  TraceFile: trace.log\n'
                'HostMetrics:\n'
                '  UserStringCommand: echo base\n'
                '  ReportInterval: 42\n'
                '  Channel: 2\n',
                encoding='utf-8',
            )
            (overlay_dir / 'later.yaml').write_text(
                'General:\n'
                '  MaxMessageQueue: 60\n'
                'Logging:\n'
                '  JSONFile: output.json\n'
                'HostMetrics:\n'
                '  Channel: 0\n',
                encoding='utf-8',
            )
            # A second partial file must not reset unrelated values from
            # either the base config or the first overlay. It deliberately
            # updates different keys so directory enumeration order is irrelevant.
            (overlay_dir / 'another.yaml').write_text(
                'General:\n'
                '  APIPort: 4405\n'
                'Logging:\n'
                '  TraceFile: second-trace.log\n',
                encoding='utf-8',
            )
            proc = subprocess.run(
                [os.environ['MESHTASTICD_BIN'], '-c', str(base), '--output-yaml'],
                cwd=root, capture_output=True, text=True, timeout=30, check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            for section, key, expected in (
                ('General', 'MaxNodes', '500'),
                ('General', 'MaxMessageQueue', '60'),
                ('General', 'MACAddress', '020000000001'),
                ('General', 'TCPPort', '4405'),
                ('Logging', 'LogLevel', 'debug'),
                ('Logging', 'TraceFile', 'second-trace.log'),
                ('Logging', 'JSONFile', 'output.json'),
                ('HostMetrics', 'UserStringCommand', 'echo base'),
                ('HostMetrics', 'ReportInterval', '42'),
                ('HostMetrics', 'Channel', '0'),
            ):
                with self.subTest(section=section, key=key):
                    self.assertEqual(emitted_value(proc.stdout, section, key),
                                     expected)


if __name__ == '__main__':
    unittest.main()
