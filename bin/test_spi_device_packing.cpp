// Standalone host regression: g++ -std=c++17 -Wall -Wextra -pedantic
//   bin/test_spi_device_packing.cpp -o /tmp/test-spi-pack && /tmp/test-spi-pack
#include "../src/platform/portduino/SpiDeviceId.h"

static_assert(portduino::packSpiDeviceId(0, 0) == 0);
static_assert(portduino::packSpiDeviceId(1, 0) == 0x01);
static_assert(portduino::packSpiDeviceId(0, 1) == 0x10);
static_assert(portduino::packSpiDeviceId(2, 3) == 0x32);
static_assert((portduino::packSpiDeviceId(2, 3) & 0x0f) == 2);
static_assert((portduino::packSpiDeviceId(2, 3) >> 4) == 3);

int main() { return 0; }
