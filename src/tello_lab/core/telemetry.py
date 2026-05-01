from __future__ import annotations

import time
from collections.abc import Callable


class BatteryMonitor:
    """Small helper that periodically reads and caches the drone battery level."""

    def __init__(
        self,
        read_battery: Callable[[], int],
        *,
        refresh_interval_seconds: float = 2.0,
    ) -> None:
        self.read_battery = read_battery
        self.refresh_interval_seconds = refresh_interval_seconds

        self.value: int | None = None
        self._last_refresh = 0.0

    def refresh(self, *, force: bool = False) -> int | None:
        """Refresh the cached battery value when needed and return it."""
        now = time.monotonic()

        if not force and now - self._last_refresh < self.refresh_interval_seconds:
            return self.value

        try:
            self.value = self.read_battery()
            self._last_refresh = now
        except Exception:
            # Keep the last known value if the drone misses a telemetry response.
            pass

        return self.value