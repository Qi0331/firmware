// Host regression: g++ -std=c++17 -Wall -Wextra -pedantic
//   bin/test_traceroute_timeout.cpp -o /tmp/test-trace-timeout && /tmp/test-trace-timeout
#include "../src/modules/TraceRouteTimeout.h"
#include <cstdint>

using traceroute_timing::timedOut;
static_assert(traceroute_timing::kTrackingTimeoutMs == 60000UL);
static_assert(!timedOut<uint32_t>(10000u, 0u, 60000u));
static_assert(!timedOut<uint32_t>(60000u, 0u, 60000u));
static_assert(timedOut<uint32_t>(60001u, 0u, 60000u));
// The same comparison must work across a 32-bit millisecond clock rollover.
static_assert(!timedOut<uint32_t>(0x00000010u, 0xfffffff0u, 60000u));
static_assert(timedOut<uint32_t>(0x00010000u, 0xfffffff0u, 60000u));

// A zero timeout still waits until at least one tick has elapsed.
static_assert(!timedOut<uint32_t>(42u, 42u, 0u));
static_assert(timedOut<uint32_t>(43u, 42u, 0u));
// Small unsigned clocks exercise the same modulo arithmetic as millis().
static_assert(!timedOut<uint16_t>(4u, 65530u, 10u));
static_assert(timedOut<uint16_t>(5u, 65530u, 10u));
// The helper is not accidentally hard-coded to a 32-bit tick type.
static_assert(timedOut<uint64_t>(60002ULL, 1ULL, 60000ULL));

int main() { return 0; }
