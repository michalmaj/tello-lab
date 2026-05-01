from __future__ import annotations

import cv2
import numpy as np


def draw_status_overlay(
    frame: np.ndarray,
    *,
    battery: int | None,
    is_flying: bool,
    controls_text: str,
) -> None:
    """Draw a simple status HUD on top of the frame."""
    status_text = "FLYING" if is_flying else "READY"
    battery_text = f"Battery: {battery}%" if battery is not None else "Battery: N/A"

    draw_text(frame, battery_text, position=(16, 32), scale=0.8)
    draw_text(frame, f"State: {status_text}", position=(16, 64), scale=0.8)
    draw_text(
        frame,
        controls_text,
        position=(16, frame.shape[0] - 20),
        scale=0.65,
        color=(255, 255, 255),
    )


def draw_text(
    frame: np.ndarray,
    text: str,
    *,
    position: tuple[int, int],
    scale: float = 0.7,
    color: tuple[int, int, int] = (0, 255, 0),
    thickness: int = 2,
) -> None:
    """Draw readable text on a video frame."""
    cv2.putText(
        frame,
        text,
        position,
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        color,
        thickness,
        cv2.LINE_AA,
    )