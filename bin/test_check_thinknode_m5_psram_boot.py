import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from check_thinknode_m5_psram_boot import last_boot_psram, validate_psram, main


class ThinkNodeM5BootLogTests(unittest.TestCase):
    def test_healthy_eight_mib_log(self):
        total, free = last_boot_psram(
            'INFO Total PSRAM: 8388608\nINFO Free PSRAM : 7340032 bytes\n')
        self.assertEqual((total, free), (8388608, 7340032))
        self.assertEqual(validate_psram(total, free), [])

    def test_zero_psram_is_rejected(self):
        total, free = last_boot_psram('Total PSRAM: 0\nFree PSRAM : 0 bytes\n')
        self.assertTrue(validate_psram(total, free))

    def test_incomplete_log_is_not_a_pass(self):
        with self.assertRaises(ValueError):
            last_boot_psram('Total PSRAM: 8388608\nboot interrupted\n')

    def test_incomplete_latest_boot_is_rejected(self):
        log = ('Total PSRAM: 8388608\nFree PSRAM: 7340032\n'
               'reboot\nTotal PSRAM: 8388608\n')
        with self.assertRaises(ValueError):
            last_boot_psram(log)

    def test_latest_complete_boot_wins(self):
        log = ('Total PSRAM: 0\nFree PSRAM: 0\n'
               'reboot\nTotal PSRAM: 8,388,608\nFree PSRAM: 7,340,032\n')
        self.assertEqual(last_boot_psram(log), (8388608, 7340032))

    def test_reboot_without_new_readings_invalidates_old_success(self):
        log = 'Total PSRAM: 8388608\nFree PSRAM: 7340032\nreboot\n'
        with self.assertRaises(ValueError):
            last_boot_psram(log)

    def test_reset_between_total_and_free_does_not_mix_boots(self):
        log = 'Total PSRAM: 8388608\nrst:0x1 (POWERON_RESET)\nFree PSRAM: 7340032\n'
        with self.assertRaises(ValueError):
            last_boot_psram(log)

    def test_non_reset_word_does_not_invalidate_log(self):
        log = 'Total PSRAM: 8388608\npreboot status\nFree PSRAM: 7340032\n'
        self.assertEqual(last_boot_psram(log), (8388608, 7340032))

    def test_impossible_free_exceeding_total_is_rejected(self):
        self.assertTrue(validate_psram(8388608, 9000000))

    def test_four_mib_is_not_eight_mib(self):
        self.assertTrue(validate_psram(4 * 1024 * 1024, 3 * 1024 * 1024))

    def test_cli_fails_on_missing_psram(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / 'boot.log'
            log.write_text('Total PSRAM: 0\nFree PSRAM: 0\n')
            with patch('sys.argv', ['check', str(log)]):
                with self.assertRaises(SystemExit) as exc:
                    main()
            self.assertEqual(exc.exception.code, 1)


if __name__ == '__main__':
    unittest.main()
