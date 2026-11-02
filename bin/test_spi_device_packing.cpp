// Standalone host regression: g++ -std=c++17 -Wall -Wextra -pedantic
//   bin/test_spi_device_packing.cpp -o /tmp/test-spi-pack && /tmp/test-spi-pack
#include "../src/platform/portduino/SpiDeviceId.h"

static_assert(portduino::packSpiDeviceId(0, 0) == 0);
static_assert(portduino::packSpiDeviceId(1, 0) == 0x01);
static_assert(portduino::packSpiDeviceId(0, 1) == 0x10);
static_assert(portduino::packSpiDeviceId(2, 3) == 0x32);
static_assert((portduino::packSpiDeviceId(2, 3) & 0x0f) == 2);
static_assert((portduino::packSpiDeviceId(2, 3) >> 4) == 3);

// Exhaustively cover the representable spidev<bus>.<device> nibble space.
// Every pair must round-trip and must encode to a unique byte.
constexpr bool allSpiPairsRoundTrip()
{
    bool seen[256] = {};
    for (int device = 0; device < 16; ++device) {
        for (int bus = 0; bus < 16; ++bus) {
            const int packed = portduino::packSpiDeviceId(bus, device);
            if (packed < 0 || packed > 255 || (packed & 15) != bus ||
                ((packed >> 4) & 15) != device || seen[packed])
                return false;
            seen[packed] = true;
        }
    }
    return true;
}
static_assert(allSpiPairsRoundTrip(), "SPI bus/device nibble encoding must be bijective");

int main() { return 0; }
