# ThinkNode M5 N4R8 PSRAM validation (experimental)

Related issue: meshtastic/firmware#12117. This document is a **test plan**, not a record of a successful build or hardware test. The candidate changes the ESP32-S3 memory mode to `qio_opi` and enables `BOARD_HAS_PSRAM`; neither setting proves the physical PSRAM bus mode.

## Before flashing

1. Confirm the exact ESP32-S3 module marking, flash size (4 MB), PSRAM size (8 MB), and PSRAM interface from the physical board or manufacturer documentation. Do not infer octal mode from the capacity alone.
2. Preserve the currently working firmware and configuration; arrange a recovery path. Do not flash the candidate onto an unidentified module.
3. Use a clean checkout of this branch and record the Git commit, PlatformIO version, framework/toolchain versions, device revision, and serial baud rate.

## Reproducible build checks

From the repository root:

```sh
python -m unittest bin/test_thinknode_m5_psram_config.py
pio run -e thinknode_m5
pio run -e thinknode_m5-inkhud
```

Record both command exit codes and complete logs. Check that the build resolves `boards/ThinkNode-M5-N4R8.json`, uses 4 MB flash, and does not report PSRAM/flash-mode incompatibility. A passing static check is **not** a passing firmware build.

## Hardware acceptance checks (only after module verification)

1. Flash the non-InkHUD build through the project's documented recovery-capable workflow. Capture a complete cold-boot serial log and watch for boot loops, flash read failures, and PSRAM initialization errors.
2. Record `Total PSRAM` and `Free PSRAM` if the build emits those fields. Both must be positive and the total should be consistent with the verified 8 MB device; a zero value is a failure.
3. Exercise normal display updates, BLE connections, and the node database while watching heap/PSRAM statistics. Repeat after a cold power cycle.
4. Repeat for `thinknode_m5-inkhud`. Verify that both firmware variants boot and that InkHUD rendering is stable.
5. Compare against a known-good official N4 build on the **same hardware**. Record differences in boot, radio, memory availability, and stability.

## Evidence and stop conditions

Attach exact build commands, logs, module marking or manufacturer specification, serial boot logs, and firmware commit. Stop and revert on boot failure, unexpected flash size, PSRAM initialization failure, or regression in radio/display/BLE behavior.

Until the build and physical validation are complete, keep this branch experimental and **do not open an upstream PR**. Disclose GPT-6 assistance if eventually proposed for review.
