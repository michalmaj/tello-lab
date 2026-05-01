from __future__ import annotations

import numpy as np

from tello_lab.core.runtime import DemoRuntime
from tello_lab.ui.overlay import draw_text

WINDOW_NAME = "tello-lab | 01_keyboard_flight"

RC_SPEED = 35
YAW_SPEED = 45

CONTROLS_TEXT = (
    "Controls: [t] takeoff  [l] land  [q] quit\n"
    "Move: [w/s/a/d] horizontal  [r/f] up/down\n"
    "Yaw: [left/right arrows] rotate  [space] hover"
)


def draw_command_overlay(frame: np.ndarray, runtime: DemoRuntime) -> None:
    """Draw the current RC command on top of the frame."""
    if runtime.manual_control is None:
        return

    command = runtime.manual_control.current_command
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
    runtime = DemoRuntime(
        window_name=WINDOW_NAME,
        controls_text=CONTROLS_TEXT,
        movement_enabled=True,
        speed=RC_SPEED,
        yaw_speed=YAW_SPEED,
    )
    runtime.run(draw_extra_overlay=draw_command_overlay)


if __name__ == "__main__":
    main()