from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import cv2

from tello_lab.control.commands import ControlCommand


class KeyboardAction(str, Enum):
    """High-level keyboard actions shared by demos."""

    NONE = "none"
    TAKEOFF = "takeoff"
    LAND = "land"
    QUIT = "quit"


@dataclass(frozen=True)
class KeyboardInput:
    """A decoded keyboard input event."""

    action: KeyboardAction = KeyboardAction.NONE
    command: ControlCommand | None = None


ARROW_UP_CODES = {2490368, 63232, 65362}
ARROW_DOWN_CODES = {2621440, 63233, 65364}
ARROW_LEFT_CODES = {2424832, 63234, 65361}
ARROW_RIGHT_CODES = {2555904, 63235, 65363}


def read_keyboard_action(delay_ms: int = 1) -> KeyboardAction:
    """Read a keyboard key from an OpenCV window and map it to a demo action."""
    key = read_key_code(delay_ms=delay_ms)

    if key is None:
        return KeyboardAction.NONE

    return decode_keyboard_action(key)


def read_keyboard_input(
    *,
    speed: int,
    yaw_speed: int,
    delay_ms: int = 1,
) -> KeyboardInput:
    """Read and decode a keyboard input event."""
    key = read_key_code(delay_ms=delay_ms)

    if key is None:
        return KeyboardInput()

    return KeyboardInput(
        action=decode_keyboard_action(key),
        command=decode_movement_command(key, speed=speed, yaw_speed=yaw_speed),
    )


def read_key_code(delay_ms: int = 1) -> int | None:
    """Read a raw key code from an OpenCV window."""
    key = cv2.waitKeyEx(delay_ms)

    if key == -1:
        return None

    return key


def decode_keyboard_action(key: int) -> KeyboardAction:
    """Decode an OpenCV key code into a high-level keyboard action."""
    char = key_to_char(key)

    if char == "t":
        return KeyboardAction.TAKEOFF

    if char == "l":
        return KeyboardAction.LAND

    if char == "q":
        return KeyboardAction.QUIT

    return KeyboardAction.NONE


def decode_movement_command(
    key: int,
    *,
    speed: int,
    yaw_speed: int,
) -> ControlCommand | None:
    """Decode an OpenCV key code into a movement command."""
    char = key_to_char(key)

    if char == " ":
        return ControlCommand.hover()

    if char == "w" or key in ARROW_UP_CODES:
        return ControlCommand.forward(speed)

    if char == "s" or key in ARROW_DOWN_CODES:
        return ControlCommand.backward(speed)

    if char == "a":
        return ControlCommand.left(speed)

    if char == "d":
        return ControlCommand.right(speed)

    if char == "r":
        return ControlCommand.up(speed)

    if char == "f":
        return ControlCommand.down(speed)

    if key in ARROW_LEFT_CODES:
        return ControlCommand.yaw_left(yaw_speed)

    if key in ARROW_RIGHT_CODES:
        return ControlCommand.yaw_right(yaw_speed)

    return None


def key_to_char(key: int) -> str | None:
    """Convert an OpenCV key code to a lowercase character when possible."""
    normalized_key = key & 0xFF

    try:
        return chr(normalized_key).lower()
    except ValueError:
        return None