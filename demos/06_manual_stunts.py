from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from tello_lab.control.commands import ControlCommand
from tello_lab.control.keyboard import (
    KeyboardAction,
    decode_keyboard_action,
    decode_movement_command,
    key_to_char,
    read_key_code,
)
from tello_lab.control.stunts import StuntExecutor, decode_stunt_action
from tello_lab.core.drone import TelloDrone
from tello_lab.core.telemetry import BatteryMonitor
from tello_lab.paths import PROJECT_ROOT
from tello_lab.ui.overlay import draw_status_overlay, draw_text

WINDOW_NAME = "tello-lab | 06_manual_stunts"

RC_SEND_INTERVAL_SECONDS = 0.05
COMMAND_TIMEOUT_SECONDS = 0.35

SNAPSHOT_DIR = PROJECT_ROOT / "recordings" / "snapshots"

CONTROLS_TEXT = (
    "Flight: [t] takeoff  [l] land  [q] quit  [space] hover\n"
    "Move: [w/s/a/d] horizontal  [r/f] up/down  [arrows] forward/back/yaw\n"
    "Stunts: [z/x] flip L/R  [c/v] flip F/B  [e/g] spin CW/CCW  [b] bounce  [p] photo"
)


@dataclass(frozen=True)
class SpeedMode:
    """Manual flight speed mode."""

    name: str
    movement_speed: int
    yaw_speed: int


SPEED_MODES = {
    "1": SpeedMode(name="slow", movement_speed=22, yaw_speed=30),
    "2": SpeedMode(name="normal", movement_speed=35, yaw_speed=45),
    "3": SpeedMode(name="sport", movement_speed=55, yaw_speed=70),
}


def draw_manual_stunts_overlay(
    frame: np.ndarray,
    *,
    battery: int | None,
    is_flying: bool,
    current_command: ControlCommand,
    speed_mode: SpeedMode,
    stunt_executor: StuntExecutor,
) -> None:
    """Draw manual stunt demo overlay."""
    draw_status_overlay(
        frame,
        battery=battery,
        is_flying=is_flying,
        controls_text=CONTROLS_TEXT,
    )

    draw_text(
        frame,
        (
            f"RC: lr={current_command.left_right:+d} "
            f"fb={current_command.forward_back:+d} "
            f"ud={current_command.up_down:+d} "
            f"yaw={current_command.yaw:+d}"
        ),
        position=(16, 96),
        scale=0.65,
        color=(255, 255, 255),
    )

    draw_text(
        frame,
        (
            f"Speed: {speed_mode.name} "
            f"(move={speed_mode.movement_speed}, yaw={speed_mode.yaw_speed}) "
            "[1/2/3]"
        ),
        position=(16, 124),
        scale=0.65,
        color=(255, 255, 255),
    )

    draw_text(
        frame,
        f"Last stunt: {stunt_executor.last_message}",
        position=(16, 152),
        scale=0.60,
        color=(255, 255, 255),
    )


def land_if_needed(drone: TelloDrone, is_flying: bool) -> bool:
    """Land the drone if needed."""
    if not is_flying:
        return False

    try:
        print("Landing...")
        drone.tello.send_rc_control(0, 0, 0, 0)
        drone.tello.land()
    except Exception as error:
        print(f"Landing failed: {error}")

    return False


def takeoff_if_needed(drone: TelloDrone, is_flying: bool) -> bool:
    """Take off if needed."""
    if is_flying:
        return True

    print("Takeoff...")
    drone.tello.takeoff()
    return True


def main() -> None:
    """Run a manual stunt flight demo."""
    drone = TelloDrone()

    battery: int | None = None
    is_flying = False

    speed_mode = SPEED_MODES["2"]
    current_command = ControlCommand.hover()
    last_command_update = time.monotonic()
    last_rc_send = 0.0

    stunt_executor = StuntExecutor(
        min_flip_battery_percent=40,
        min_stunt_battery_percent=25,
        cooldown_seconds=4.0,
        bounce_distance_cm=30,
        snapshot_dir=SNAPSHOT_DIR,
    )

    try:
        drone.connect()

        battery_monitor = BatteryMonitor(drone.tello.get_battery)
        battery = battery_monitor.refresh(force=True)
        print(f"Connected. Battery: {battery if battery is not None else 'N/A'}%")

        drone.start_video()

        while True:
            frame = drone.frame

            if frame is None:
                time.sleep(0.01)
                continue

            now = time.monotonic()
            battery = battery_monitor.refresh()

            display_frame = frame.copy()
            draw_manual_stunts_overlay(
                display_frame,
                battery=battery,
                is_flying=is_flying,
                current_command=current_command,
                speed_mode=speed_mode,
                stunt_executor=stunt_executor,
            )

            cv2.imshow(WINDOW_NAME, display_frame)

            key_code = read_key_code()
            key_char = key_to_char(key_code) if key_code is not None else None

            if key_char in SPEED_MODES:
                speed_mode = SPEED_MODES[key_char]
                print(f"Speed mode: {speed_mode.name}")

            action = decode_keyboard_action(key_code) if key_code is not None else KeyboardAction.NONE

            if action == KeyboardAction.TAKEOFF:
                is_flying = takeoff_if_needed(drone, is_flying)
                current_command = ControlCommand.hover()
                last_command_update = now

            elif action == KeyboardAction.LAND:
                is_flying = land_if_needed(drone, is_flying)
                current_command = ControlCommand.hover()

            elif action == KeyboardAction.QUIT:
                is_flying = land_if_needed(drone, is_flying)
                print("Exiting manual stunt demo.")
                break

            stunt_action = decode_stunt_action(key_char)
            if stunt_action.value != "none":
                stunt_executor.execute(
                    stunt_action,
                    tello=drone.tello,
                    is_flying=is_flying,
                    battery=battery,
                    frame=frame,
                )
                current_command = ControlCommand.hover()
                last_command_update = now

            movement_command = (
                decode_movement_command(
                    key_code,
                    speed=speed_mode.movement_speed,
                    yaw_speed=speed_mode.yaw_speed,
                )
                if key_code is not None
                else None
            )

            if movement_command is not None:
                current_command = movement_command
                last_command_update = now

            if now - last_command_update > COMMAND_TIMEOUT_SECONDS:
                current_command = ControlCommand.hover()

            if is_flying and now - last_rc_send >= RC_SEND_INTERVAL_SECONDS:
                drone.tello.send_rc_control(*current_command.as_tuple())
                last_rc_send = now

    except KeyboardInterrupt:
        print("Interrupted by user.")
        is_flying = land_if_needed(drone, is_flying)

    finally:
        if is_flying:
            land_if_needed(drone, is_flying)

        cv2.destroyAllWindows()
        drone.close()


if __name__ == "__main__":
    main()