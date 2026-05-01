from __future__ import annotations

import time

import cv2
from djitellopy import Tello

from tello_lab.control.commands import ControlCommand
from tello_lab.control.keyboard import KeyboardAction, read_keyboard_input
from tello_lab.ui.overlay import draw_status_overlay, draw_text

WINDOW_NAME = "tello-lab | 01_keyboard_flight"

BATTERY_REFRESH_SECONDS = 2.0
RC_SEND_INTERVAL_SECONDS = 0.05
COMMAND_TIMEOUT_SECONDS = 0.35

RC_SPEED = 35
YAW_SPEED = 45

CONTROLS_TEXT = (
    "Controls: [t] takeoff  [l] land  [q] quit\n"
    "Move: [w/s/a/d] horizontal  [r/f] up/down\n"
    "Yaw: [left/right arrows] rotate  [space] hover"
)


def draw_command_overlay(frame, command: ControlCommand) -> None:
    """Draw the current RC command on top of the frame."""
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


def land_if_needed(tello: Tello, is_flying: bool) -> bool:
    """Land the drone if it is currently flying."""
    if not is_flying:
        return False

    try:
        print("Landing...")
        tello.send_rc_control(0, 0, 0, 0)
        tello.land()
    except Exception as error:
        print(f"Landing failed: {error}")

    return False


def main() -> None:
    """Run a keyboard-controlled Tello flight demo."""
    tello = Tello()
    frame_read = None

    is_flying = False
    battery: int | None = None

    current_command = ControlCommand.hover()
    last_command_update = 0.0
    last_battery_refresh = 0.0
    last_rc_send = 0.0

    try:
        print("Connecting to Tello...")
        tello.connect()

        battery = tello.get_battery()
        print(f"Connected. Battery: {battery}%")

        print("Starting video stream...")
        tello.streamon()
        frame_read = tello.get_frame_read()

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

            keyboard_input = read_keyboard_input(
                speed=RC_SPEED,
                yaw_speed=YAW_SPEED,
            )

            if keyboard_input.action == KeyboardAction.TAKEOFF:
                if not is_flying:
                    print("Takeoff...")
                    tello.takeoff()
                    is_flying = True
                    current_command = ControlCommand.hover()
                    last_command_update = now

            elif keyboard_input.action == KeyboardAction.LAND:
                is_flying = land_if_needed(tello, is_flying)
                current_command = ControlCommand.hover()

            elif keyboard_input.action == KeyboardAction.QUIT:
                if is_flying:
                    print("Landing before exit...")
                    is_flying = land_if_needed(tello, is_flying)
                print("Exiting keyboard flight demo.")
                break

            if keyboard_input.command is not None:
                current_command = keyboard_input.command
                last_command_update = now

            if now - last_command_update > COMMAND_TIMEOUT_SECONDS:
                current_command = ControlCommand.hover()

            if is_flying and now - last_rc_send >= RC_SEND_INTERVAL_SECONDS:
                tello.send_rc_control(*current_command.as_tuple())
                last_rc_send = now

            display_frame = frame.copy()
            draw_status_overlay(
                display_frame,
                battery=battery,
                is_flying=is_flying,
                controls_text=CONTROLS_TEXT,
            )
            draw_command_overlay(display_frame, current_command)

            cv2.imshow(WINDOW_NAME, display_frame)

    except KeyboardInterrupt:
        print("Interrupted by user.")
        is_flying = land_if_needed(tello, is_flying)

    finally:
        if is_flying:
            land_if_needed(tello, is_flying)

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