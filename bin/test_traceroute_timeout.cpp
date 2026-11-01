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

int main() { return 0; }
