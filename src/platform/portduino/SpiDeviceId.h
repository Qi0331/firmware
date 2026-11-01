#pragma once

// framework-portduino's HardwareSPI decodes the low nibble as the SPI bus
// and the high nibble as the chip-select device (spidev<bus>.<device>).
namespace portduino {
constexpr int packSpiDeviceId(int bus, int device)
{
    return bus | (device << 4);
}
} // namespace portduino
