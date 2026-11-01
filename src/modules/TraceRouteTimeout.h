#pragma once

#include <type_traits>

namespace traceroute_timing {
// A 10-second UI timeout discards valid multi-hop/retransmitted replies on slow presets.
inline constexpr unsigned long kTrackingTimeoutMs = 60000UL;

template <typename Tick> constexpr bool timedOut(Tick now, Tick started, Tick timeoutMs)
{
    static_assert(std::is_unsigned<Tick>::value, "millisecond ticks must be unsigned");
    return static_cast<Tick>(now - started) > timeoutMs;
}
} // namespace traceroute_timing
