from __future__ import annotations

import time
from collections.abc import Callable

import cv2
import numpy as np

from tello_lab.control.manual import ManualFlightController
from tello_lab.core.drone import TelloDrone
from tello_lab.core.telemetry import BatteryMonitor
from tello_lab.ui.overlay import draw_status_overlay

FrameOverlayCallback = Callable[[np.ndarray, "DemoRuntime"], None]


class DemoRuntime:
    """Reusable runtime loop for Tello demos."""

    def __init__(
        self,
        *,
        window_name: str,
        controls_text: str,
        movement_enabled: bool = False,
        speed: int = 35,
        yaw_speed: int = 45,
        empty_frame_sleep_seconds: float = 0.01,
    ) -> None:
        self.window_name = window_name
        self.controls_text = controls_text
        self.movement_enabled = movement_enabled
        self.speed = speed
        self.yaw_speed = yaw_speed
        self.empty_frame_sleep_seconds = empty_frame_sleep_seconds

        self.drone = TelloDrone()
        self.manual_control: ManualFlightController | None = None
        self.battery_monitor: BatteryMonitor | None = None
        self.battery: int | None = None

    def run(
        self,
        *,
        draw_extra_overlay: FrameOverlayCallback | None = None,
    ) -> None:
        """Run the demo loop."""
        try:
            self._setup()

            while True:
                frame = self.drone.frame

                if frame is None:
                    time.sleep(self.empty_frame_sleep_seconds)
                    continue

                self._refresh_battery()

                display_frame = frame.copy()
                self._draw_base_overlay(display_frame)

                if draw_extra_overlay is not None:
                    draw_extra_overlay(display_frame, self)

                cv2.imshow(self.window_name, display_frame)

                update = self._tick_manual_control()

                if update.should_quit:
                    print(f"Exiting {self.window_name}.")
                    break

        except KeyboardInterrupt:
            print("Interrupted by user.")

        finally:
            self.shutdown()

    def shutdown(self) -> None:
        """Safely stop the runtime."""
        if self.manual_control is not None:
            self.manual_control.shutdown()

        cv2.destroyAllWindows()
        self.drone.close()

    def _setup(self) -> None:
        self.drone.connect()

        self.battery_monitor = BatteryMonitor(self.drone.tello.get_battery)
        self.battery = self.battery_monitor.refresh(force=True)
        print(f"Connected. Battery: {self.battery if self.battery is not None else 'N/A'}%")

        self.drone.start_video()

        self.manual_control = ManualFlightController(
            self.drone.tello,
            movement_enabled=self.movement_enabled,
            speed=self.speed,
            yaw_speed=self.yaw_speed,
        )

    def _refresh_battery(self) -> None:
        if self.battery_monitor is None:
            return

        self.battery = self.battery_monitor.refresh()

    def _draw_base_overlay(self, frame: np.ndarray) -> None:
        if self.manual_control is None:
            is_flying = False
        else:
            is_flying = self.manual_control.is_flying

        draw_status_overlay(
            frame,
            battery=self.battery,
            is_flying=is_flying,
            controls_text=self.controls_text,
        )

    def _tick_manual_control(self):
        if self.manual_control is None:
            raise RuntimeError("Manual control is not initialized.")

        return self.manual_control.tick()