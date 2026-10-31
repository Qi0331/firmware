import tempfile
import unittest
from pathlib import Path
from check_hardware_names import api_names, firmware_names, compare


class HardwareNameAuditTests(unittest.TestCase):
    def test_extract_api_entries(self):
        text = '''export const deviceHardwareList = [
        {
          platformioTarget: "a-board",
          architecture: "esp32",
          displayName: "Board A",
        },
        {
          platformioTarget: 'board-b',
          displayName: 'Board B',
        },
        ]'''
        self.assertEqual(api_names(text), {'a-board': 'Board A', 'board-b': 'Board B'})

    def test_ts_comments_do_not_inject_fake_hardware_names(self):
        text = '''export const devices = [
          /* {
            platformioTarget: "fake",
            displayName: "Fake Board",
          }, */
          {
            platformioTarget: "board-a", /* displayName: "Wrong" */
            displayName: "Board A // Pro",
          },
          {
            platformioTarget: 'board-b', // displayName: 'Wrong'
            displayName: 'Board B',
          },
        ]'''
        self.assertEqual(api_names(text),
                         {'board-a': 'Board A // Pro', 'board-b': 'Board B'})

    def test_conflicting_firmware_names_are_reported_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for variant, name in (('one', 'First'), ('two', 'Second')):
                target = root / 'variants' / variant / 'platformio.ini'
                target.parent.mkdir(parents=True)
                target.write_text(
                    '[env:shared-board]\n'
                    f'custom_meshtastic_display_name = {name}\n'
                )
            firmware = firmware_names(root)
            self.assertIsNone(firmware['shared-board'])
            result = compare(firmware, {'shared-board': 'First'})
            self.assertEqual(result['ambiguous_firmware_targets'], ['shared-board'])
            self.assertEqual(result['compared'], 0)
            self.assertEqual(result['mismatched'], [])

    def test_repeated_identical_firmware_name_is_not_ambiguous(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for variant in ('one', 'two'):
                target = root / 'variants' / variant / 'platformio.ini'
                target.parent.mkdir(parents=True)
                target.write_text(
                    '[env:shared-board]\n'
                    'custom_meshtastic_display_name = Same\n'
                )
            self.assertEqual(firmware_names(root), {'shared-board': 'Same'})

    def test_extract_variant_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'variants/esp32/test/platformio.ini'
            target.parent.mkdir(parents=True)
            target.write_text('[env:a-board]\ncustom_meshtastic_display_name = Board A\n'
                              '[env:b-board]\nboard_level = pr\n')
            self.assertEqual(firmware_names(Path(tmp)), {'a-board': 'Board A'})

    def test_ambiguous_api_target_is_not_silently_overwritten(self):
        text = '''export const devices = [
          {
            platformioTarget: "native",
            displayName: "RAK6421 Hat+",
          },
          {
            platformioTarget: "native",
            displayName: "Elecrow Meshstick 1262",
          },
          {
            platformioTarget: "board-a",
            displayName: "Board A",
          },
        ]'''
        names = api_names(text)
        self.assertIsNone(names['native'])
        result = compare({'native': 'Native', 'board-a': 'Board A'}, names)
        self.assertEqual(result['ambiguous_api_targets'], ['native'])
        self.assertEqual(result['mismatched'], [])
        self.assertEqual(result['matched'], 1)
        self.assertEqual(result['compared'], 1)

    def test_non_env_section_does_not_leak_into_previous_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'variants/esp32/test/platformio.ini'
            target.parent.mkdir(parents=True)
            target.write_text(
                '[env:board-a]\ncustom_meshtastic_display_name = Board A\n'
                '[common]\ncustom_meshtastic_display_name = Not a board\n'
                '[env:board-b]\ncustom_meshtastic_display_name = Board B\n'
            )
            self.assertEqual(firmware_names(Path(tmp)),
                             {'board-a': 'Board A', 'board-b': 'Board B'})

    def test_commented_api_fields_do_not_override_real_values(self):
        text = '''{
          platformioTarget: "board-a",
          // displayName: "Obsolete",
          displayName: "Board A",
        },'''
        self.assertEqual(api_names(text), {'board-a': 'Board A'})

    def test_ambiguous_api_target_is_a_strict_failure(self):
        # A duplicate target must not make --strict appear clean when the
        # conflicting display names cannot be compared meaningfully.
        import contextlib
        import io
        import json
        import sys
        from unittest.mock import patch
        from check_hardware_names import main

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ini = root / 'variants/test/platformio.ini'
            ini.parent.mkdir(parents=True)
            ini.write_text('[env:board-a]\ncustom_meshtastic_display_name = Board A\n')
            resource = root / 'resource.ts'
            resource.write_text('''{\nplatformioTarget: "board-a",\ndisplayName: "One",\n},
{\nplatformioTarget: "board-a",\ndisplayName: "Two",\n},''')
            output = io.StringIO()
            with patch.object(sys, 'argv', ['audit', '--strict',
                                             '--firmware-root', str(root),
                                             '--api-resource', str(resource)]):
                with contextlib.redirect_stdout(output):
                    with self.assertRaises(SystemExit) as exc:
                        main()
            self.assertEqual(exc.exception.code, 1)
            self.assertEqual(json.loads(output.getvalue())['ambiguous_api_targets'],
                             ['board-a'])

    def test_compare_names_and_absences(self):
        actual = compare({'a': 'One', 'b': 'Two', 'c': 'Three'},
                         {'a': 'One', 'b': 'TWO', 'd': 'Four'})
        self.assertEqual(actual['ambiguous_api_targets'], [])
        self.assertEqual(actual['matched'], 1)
        self.assertEqual(actual['compared'], 2)
        self.assertEqual(actual['mismatched'], [{'target': 'b', 'firmware': 'Two', 'api': 'TWO'}])
        self.assertEqual(actual['api_without_firmware_display_name'], ['d'])
        self.assertEqual(actual['firmware_only_display_name'], ['c'])


if __name__ == '__main__':
    unittest.main()
