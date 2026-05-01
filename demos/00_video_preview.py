from __future__ import annotations

import time

import cv2
from djitellopy import Tello

from tello_lab.control.manual import ManualFlightController
from tello_lab.ui.overlay import draw_status_overlay

WINDOW_NAME = "tello-lab | 00_video_preview"
BATTERY_REFRESH_SECONDS = 2.0
CONTROLS_TEXT = "Controls: [t] takeoff  [l] land  [q] quit"


def main() -> None:
    """Run a minimal live preview loop for the Tello drone."""
    tello = Tello()
    frame_read = None
    battery: int | None = None
    last_battery_refresh = 0.0
    manual_control: ManualFlightController | None = None

    try:
        print("Connecting to Tello...")
        tello.connect()

        battery = tello.get_battery()
        print(f"Connected. Battery: {battery}%")

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

            now = time.monotonic()
            if now - last_battery_refresh >= BATTERY_REFRESH_SECONDS:
                try:
                    battery = tello.get_battery()
                except Exception:
                    pass
                last_battery_refresh = now

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