from __future__ import annotations

import time

import cv2
from djitellopy import Tello

from tello_lab.control.manual import ManualFlightController
from tello_lab.core.telemetry import BatteryMonitor
from tello_lab.ui.overlay import draw_status_overlay

WINDOW_NAME = "tello-lab | 00_video_preview"
CONTROLS_TEXT = "Controls: [t] takeoff  [l] land  [q] quit"


def main() -> None:
    """Run a minimal live preview loop for the Tello drone."""
    tello = Tello()
    frame_read = None
    manual_control: ManualFlightController | None = None

    try:
        print("Connecting to Tello...")
        tello.connect()

        battery_monitor = BatteryMonitor(tello.get_battery)
        battery = battery_monitor.refresh(force=True)
        print(f"Connected. Battery: {battery if battery is not None else 'N/A'}%")

        print("Starting video stream...")
        tello.streamon()
        frame_read = tello.get_frame_read()

        manual_control = ManualFlightController(
            tello,
            movement_enabled=False,
        )

        while True:
            frame = frame_read.frame

            if frame is None:
                time.sleep(0.01)
                continue

            battery = battery_monitor.refresh()

            display_frame = frame.copy()
            draw_status_overlay(
                display_frame,
                battery=battery,
                is_flying=manual_control.is_flying,
                controls_text=CONTROLS_TEXT,
            )
            cv2.imshow(WINDOW_NAME, display_frame)

            update = manual_control.tick()

            if update.should_quit:
                print("Exiting preview loop.")
                break

    except KeyboardInterrupt:
        print("Interrupted by user.")
        if manual_control is not None:
            manual_control.shutdown()

    finally:
        if manual_control is not None:
            manual_control.shutdown()

        cv2.destroyAllWindows()

        try:
            tello.streamoff()
        except Exception:
            pass

        try:
            tello.end()
        except Exception:
            pass


if __name__ == "__main__":
    main()