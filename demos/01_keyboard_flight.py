from __future__ import annotations

import time

import cv2
from djitellopy import Tello

from tello_lab.control.manual import ManualFlightController
from tello_lab.ui.overlay import draw_status_overlay, draw_text

WINDOW_NAME = "tello-lab | 01_keyboard_flight"

BATTERY_REFRESH_SECONDS = 2.0

RC_SPEED = 35
YAW_SPEED = 45

CONTROLS_TEXT = (
    "Controls: [t] takeoff  [l] land  [q] quit\n"
    "Move: [w/s/a/d] horizontal  [r/f] up/down\n"
    "Yaw: [left/right arrows] rotate  [space] hover"
)


def draw_command_overlay(frame, manual_control: ManualFlightController) -> None:
    """Draw the current RC command on top of the frame."""
    command = manual_control.current_command
    command_text = (
        f"RC: lr={command.left_right:+d} "
        f"fb={command.forward_back:+d} "
        f"ud={command.up_down:+d} "
        f"yaw={command.yaw:+d}"
    )

    draw_text(
        frame,
        command_text,
        position=(16, 96),
        scale=0.65,
        color=(255, 255, 255),
    )


def main() -> None:
    """Run a keyboard-controlled Tello flight demo."""
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
            movement_enabled=True,
            speed=RC_SPEED,
            yaw_speed=YAW_SPEED,
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
            draw_command_overlay(display_frame, manual_control)

            cv2.imshow(WINDOW_NAME, display_frame)

            update = manual_control.tick()

            if update.should_quit:
                print("Exiting keyboard flight demo.")
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