#!/usr/bin/env python3
"""Static consistency checks for the experimental ThinkNode M5 PSRAM board.

These checks do NOT prove that the device has octal PSRAM or that firmware
boots. A real M5 and a PlatformIO build are required before upstream review.
"""
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = 'ThinkNode-M5-N4R8'


def env_body(ini_text, env_name):
    match = re.search(
        r'^\[env:' + re.escape(env_name) + r'\]\s*\n(.*?)(?=^\[|\Z)',
        ini_text, flags=re.MULTILINE | re.DOTALL,
    )
    if not match:
        raise AssertionError(f'Missing environment: {env_name}')
    return match.group(1)


class ThinkNodeM5PsramConfigTests(unittest.TestCase):
    def test_board_defines_octal_psram_without_changing_flash_size(self):
        board = json.loads((ROOT / 'boards' / (BOARD + '.json')).read_text())
        build = board['build']
        self.assertEqual(build['mcu'], 'esp32s3')
        self.assertEqual(build['arduino']['memory_type'], 'qio_opi')
        self.assertEqual(build['psram_type'], 'qio_opi')
        self.assertIn('-D BOARD_HAS_PSRAM', build['extra_flags'])
        self.assertEqual(board['upload']['flash_size'], '4MB')
        self.assertEqual(board['upload']['maximum_size'], 4194304)

    def test_psram_board_preserves_original_n4_hardware_settings(self):
        # Only the PSRAM-specific build settings should differ from the
        # original N4 board; changing pin-independent upload/debug settings
        # would introduce unrelated risk to an unverified hardware change.
        original = json.loads((ROOT / 'boards/ESP32-S3-WROOM-1-N4.json').read_text())
        candidate = json.loads((ROOT / 'boards' / (BOARD + '.json')).read_text())
        for key in ('upload', 'connectivity', 'debug', 'frameworks'):
            with self.subTest(key=key):
                self.assertEqual(candidate[key], original[key])
        expected_build = json.loads(json.dumps(original['build']))
        expected_build['arduino']['memory_type'] = 'qio_opi'
        expected_build['psram_type'] = 'qio_opi'
        expected_build['extra_flags'].append('-D BOARD_HAS_PSRAM')
        self.assertEqual(candidate['build'], expected_build)

    def test_both_m5_variants_use_the_same_psram_board(self):
        ini = (ROOT / 'variants/esp32s3/ELECROW-ThinkNode-M5/platformio.ini'
               ).read_text()
        for env in ('thinknode_m5', 'thinknode_m5-inkhud'):
            with self.subTest(env=env):
                body = env_body(ini, env)
                self.assertRegex(body, r'(?m)^board\s*=\s*' + BOARD + r'\s*$')
                self.assertRegex(body, r'(?m)^board_level\s*=\s*release\s*$')


    def test_m5_variants_do_not_override_board_memory_configuration(self):
        # PlatformIO env-level board_build.* keys can override the board JSON.
        # Reject local flash/PSRAM overrides until the real module is verified.
        ini = (ROOT / 'variants/esp32s3/ELECROW-ThinkNode-M5/platformio.ini'
               ).read_text()
        for env in ('thinknode_m5', 'thinknode_m5-inkhud'):
            with self.subTest(env=env):
                body = env_body(ini, env)
                self.assertNotRegex(
                    body,
                    r'(?m)^\s*board_build\.(?:arduino\.memory_type|psram_type|flash_mode)\s*=',
                )
                self.assertNotRegex(body, r'(?m)^\s*board_build\.flash_size\s*=')


if __name__ == '__main__':
    unittest.main()
