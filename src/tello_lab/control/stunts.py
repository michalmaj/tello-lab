from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import cv2
import numpy as np


class StuntAction(str, Enum):
    """One-shot stunt actions for the Tello drone."""

    NONE = "none"
    FLIP_LEFT = "flip_left"
    FLIP_RIGHT = "flip_right"
    FLIP_FORWARD = "flip_forward"
    FLIP_BACK = "flip_back"
    ROTATE_CW_360 = "rotate_cw_360"
    ROTATE_CCW_360 = "rotate_ccw_360"
    BOUNCE = "bounce"
    SNAPSHOT = "snapshot"


@dataclass(frozen=True)
class StuntResult:
    """Result of a requested stunt action."""

    executed: bool
    message: str


class StuntExecutor:
    """Execute one-shot flight stunts with basic safety gates."""

    def __init__(
        self,
        *,
        min_flip_battery_percent: int = 40,
        min_stunt_battery_percent: int = 25,
        cooldown_seconds: float = 4.0,
        bounce_distance_cm: int = 30,
        snapshot_dir: Path,
    ) -> None:
        self.min_flip_battery_percent = min_flip_battery_percent
        self.min_stunt_battery_percent = min_stunt_battery_percent
        self.cooldown_seconds = cooldown_seconds
        self.bounce_distance_cm = bounce_distance_cm
        self.snapshot_dir = snapshot_dir

        self._last_stunt_at = -999.0
        self.last_message = "Ready"

    def execute(
        self,
        action: StuntAction,
        *,
        tello: Any,
        is_flying: bool,
        battery: int | None,
        frame: np.ndarray | None,
    ) -> StuntResult:
        """Execute a requested stunt action."""
        if action == StuntAction.NONE:
            return StuntResult(executed=False, message=self.last_message)

        if action == StuntAction.SNAPSHOT:
            return self._save_snapshot(frame)

        if not is_flying:
            return self._reject(f"{action.value}: blocked, drone is not flying")

        if not self._cooldown_ready():
            remaining = self._cooldown_remaining()
            return self._reject(f"{action.value}: cooldown {remaining:.1f}s")

        if self._is_flip(action):
            if battery is not None and battery < self.min_flip_battery_percent:
                return self._reject(
                    f"{action.value}: blocked, battery < {self.min_flip_battery_percent}%"
                )

        elif battery is not None and battery < self.min_stunt_battery_percent:
            return self._reject(
                f"{action.value}: blocked, battery < {self.min_stunt_battery_percent}%"
            )

        try:
            self._hover(tello)

            if action == StuntAction.FLIP_LEFT:
                self._flip_left(tello)
            elif action == StuntAction.FLIP_RIGHT:
                self._flip_right(tello)
            elif action == StuntAction.FLIP_FORWARD:
                self._flip_forward(tello)
            elif action == StuntAction.FLIP_BACK:
                self._flip_back(tello)
            elif action == StuntAction.ROTATE_CW_360:
                tello.rotate_clockwise(360)
            elif action == StuntAction.ROTATE_CCW_360:
                tello.rotate_counter_clockwise(360)
            elif action == StuntAction.BOUNCE:
                tello.move_up(self.bounce_distance_cm)
                time.sleep(0.2)
                tello.move_down(self.bounce_distance_cm)
            else:
                return self._reject(f"{action.value}: unknown action")

            self._hover(tello)
            self._last_stunt_at = time.monotonic()
            return self._accept(f"{action.value}: executed")

        except Exception as error:
            return self._reject(f"{action.value}: failed: {error}")

    def _save_snapshot(self, frame: np.ndarray | None) -> StuntResult:
        if frame is None:
            return self._reject("snapshot: blocked, no frame")

        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        output_path = self.snapshot_dir / f"tello_snapshot_{timestamp}.jpg"

        cv2.imwrite(str(output_path), frame)
        return self._accept(f"snapshot: saved {output_path}")

    def _cooldown_ready(self) -> bool:
        return self._cooldown_remaining() <= 0.0

    def _cooldown_remaining(self) -> float:
        elapsed = time.monotonic() - self._last_stunt_at
        return max(0.0, self.cooldown_seconds - elapsed)

    def _accept(self, message: str) -> StuntResult:
        self.last_message = message
        print(message)
        return StuntResult(executed=True, message=message)

    def _reject(self, message: str) -> StuntResult:
        self.last_message = message
        print(message)
        return StuntResult(executed=False, message=message)

    def _hover(self, tello: Any) -> None:
        tello.send_rc_control(0, 0, 0, 0)
        time.sleep(0.1)

    def _is_flip(self, action: StuntAction) -> bool:
        return action in {
            StuntAction.FLIP_LEFT,
            StuntAction.FLIP_RIGHT,
            StuntAction.FLIP_FORWARD,
            StuntAction.FLIP_BACK,
        }

    def _flip_left(self, tello: Any) -> None:
        if hasattr(tello, "flip_left"):
            tello.flip_left()
        else:
            tello.flip("l")

    def _flip_right(self, tello: Any) -> None:
        if hasattr(tello, "flip_right"):
            tello.flip_right()
        else:
            tello.flip("r")

    def _flip_forward(self, tello: Any) -> None:
        if hasattr(tello, "flip_forward"):
            tello.flip_forward()
        else:
            tello.flip("f")

    def _flip_back(self, tello: Any) -> None:
        if hasattr(tello, "flip_back"):
            tello.flip_back()
        else:
            tello.flip("b")


def decode_stunt_action(key_char: str | None) -> StuntAction:
    """Decode a keyboard character into a stunt action."""
    if key_char == "z":
        return StuntAction.FLIP_LEFT

    if key_char == "x":
        return StuntAction.FLIP_RIGHT

    if key_char == "c":
        return StuntAction.FLIP_FORWARD

    if key_char == "v":
        return StuntAction.FLIP_BACK

    if key_char == "e":
        return StuntAction.ROTATE_CW_360

    if key_char == "g":
        return StuntAction.ROTATE_CCW_360

    if key_char == "b":
        return StuntAction.BOUNCE

    if key_char == "p":
        return StuntAction.SNAPSHOT

    return StuntAction.NONE