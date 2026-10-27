#!/usr/bin/env python3
"""Report firmware/API display-name drift without changing either source.

Usage: python bin/check_hardware_names.py --api-resource ../api/src/lib/resource.ts
"""
import argparse
import json
import re
from pathlib import Path


def api_names(text):
    """Extract simple DeviceHardware entries from resource.ts."""
    records = {}
    target = name = None
    for line in text.splitlines():
        if re.match(r'^\s*\{\s*$', line):
            target = name = None
        match = re.search(r'\bplatformioTarget:\s*[\'\"]([^\'\"]+)[\'\"]', line)
        if match:
            target = match.group(1)
        match = re.search(r'\bdisplayName:\s*[\'\"]([^\'\"]+)[\'\"]', line)
        if match:
            name = match.group(1)
        if re.match(r'^\s*\},?\s*$', line):
            if target is not None and name is not None:
                records[target] = name
            target = name = None
    return records


def firmware_names(root):
    """Read explicitly declared variant names (not inherited config values)."""
    records = {}
    for path in sorted((root / 'variants').rglob('platformio.ini')):
        env = None
        for line in path.read_text(encoding='utf-8').splitlines():
            match = re.match(r'^\s*\[env:([^\]]+)\]', line)
            if match:
                env = match.group(1)
            match = re.match(r'^\s*custom_meshtastic_display_name\s*=\s*(.+?)\s*(?:;.*)?$', line)
            if match and env is not None:
                records[env] = match.group(1).strip()
    return records


def compare(firmware, api):
    overlap = sorted(firmware.keys() & api.keys())
    return {
        'mismatched': [
            {'target': k, 'firmware': firmware[k], 'api': api[k]}
            for k in overlap if firmware[k] != api[k]
        ],
        'api_without_firmware_display_name': sorted(api.keys() - firmware.keys()),
        'firmware_only_display_name': sorted(firmware.keys() - api.keys()),
        'matched': sum(firmware[k] == api[k] for k in overlap),
        'compared': len(overlap),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--firmware-root', type=Path, default=Path('.'))
    parser.add_argument('--api-resource', type=Path, required=True,
                        help='Checkout of meshtastic/api src/lib/resource.ts')
    parser.add_argument('--strict', action='store_true',
                        help='Fail when mismatched display names exist')
    args = parser.parse_args()
    firmware = firmware_names(args.firmware_root)
    api = api_names(args.api_resource.read_text(encoding='utf-8'))
    if not firmware or not api:
        parser.error('No display names found; check both input paths')
    result = compare(firmware, api)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.strict and result['mismatched']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
