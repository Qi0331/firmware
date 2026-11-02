#!/usr/bin/env python3
"""Check a captured ThinkNode M5 serial boot log for usable 8 MiB PSRAM.

This is a log check, not proof of stable PSRAM operation or a hardware test.
Usage: python bin/check_thinknode_m5_psram_boot.py boot.log
"""
import argparse
import re
from pathlib import Path

TOTAL = re.compile(r'\bTotal PSRAM\s*:\s*([\d,]+)\b', re.IGNORECASE)
FREE = re.compile(r'\bFree PSRAM\s*:\s*([\d,]+)\b', re.IGNORECASE)
MIN_TOTAL_BYTES = 7 * 1024 * 1024
BOOT_MARKER = re.compile(r'\breboot\b|\brst:0x[0-9a-f]+|\bESP-ROM:', re.IGNORECASE)


def last_boot_psram(log):
    """Return the last complete total/free pair; do not mix different boots."""
    pending_total = None
    last_pair = None
    for line in log.splitlines():
        if BOOT_MARKER.search(line):
            pending_total = None
            last_pair = None
            continue
        total = TOTAL.search(line)
        if total:
            pending_total = int(total.group(1).replace(',', ''))
            last_pair = None  # A later incomplete boot must not inherit an old pass.
            continue
        free = FREE.search(line)
        if free and pending_total is not None:
            last_pair = pending_total, int(free.group(1).replace(',', ''))
            pending_total = None
    if last_pair is None:
        raise ValueError('No complete Total PSRAM / Free PSRAM pair found')
    return last_pair


def validate_psram(total, free):
    """Return a list of violations; zero or impossible readings must fail."""
    problems = []
    if total < MIN_TOTAL_BYTES:
        problems.append(f'Total PSRAM {total} bytes is below 7 MiB')
    if free <= 0:
        problems.append(f'Free PSRAM must be positive (got {free})')
    if free > total:
        problems.append(f'Free PSRAM {free} exceeds total {total}')
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path, help='Captured serial boot log')
    args = parser.parse_args()
    try:
        total, free = last_boot_psram(args.log.read_text(encoding='utf-8', errors='replace'))
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    problems = validate_psram(total, free)
    print(f'Total PSRAM: {total} bytes; Free PSRAM: {free} bytes')
    for problem in problems:
        print(f'FAIL: {problem}')
    if problems:
        raise SystemExit(1)
    print('PASS: boot log reports usable PSRAM; stability remains unverified')


if __name__ == '__main__':
    main()
