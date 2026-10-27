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

    def test_extract_variant_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'variants/esp32/test/platformio.ini'
            target.parent.mkdir(parents=True)
            target.write_text('[env:a-board]\ncustom_meshtastic_display_name = Board A\n'
                              '[env:b-board]\nboard_level = pr\n')
            self.assertEqual(firmware_names(Path(tmp)), {'a-board': 'Board A'})

    def test_compare_names_and_absences(self):
        actual = compare({'a': 'One', 'b': 'Two', 'c': 'Three'},
                         {'a': 'One', 'b': 'TWO', 'd': 'Four'})
        self.assertEqual(actual['matched'], 1)
        self.assertEqual(actual['compared'], 2)
        self.assertEqual(actual['mismatched'], [{'target': 'b', 'firmware': 'Two', 'api': 'TWO'}])
        self.assertEqual(actual['api_without_firmware_display_name'], ['d'])
        self.assertEqual(actual['firmware_only_display_name'], ['c'])


if __name__ == '__main__':
    unittest.main()
