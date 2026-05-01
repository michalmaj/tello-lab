from __future__ import annotations

from enum import Enum

import cv2


class KeyboardAction(str, Enum):
    """High-level keyboard actions shared by demos."""

    NONE = "none"
    TAKEOFF = "takeoff"
    LAND = "land"
    QUIT = "quit"


def read_keyboard_action(delay_ms: int = 1) -> KeyboardAction:
    """Read a keyboard key from an OpenCV window and map it to a demo action."""
    key = cv2.waitKey(delay_ms)

    if key == -1:
        return KeyboardAction.NONE

    return decode_keyboard_action(key)


def decode_keyboard_action(key: int) -> KeyboardAction:
    """Decode an OpenCV key code into a high-level keyboard action."""
    normalized_key = key & 0xFF

    if normalized_key == ord("t"):
        return KeyboardAction.TAKEOFF

    if normalized_key == ord("l"):
        return KeyboardAction.LAND

    if normalized_key == ord("q"):
        return KeyboardAction.QUIT

    return KeyboardAction.NONE