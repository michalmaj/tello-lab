from __future__ import annotations

from tello_lab.paths import HAND_LANDMARKER_MODEL_PATH

import cv2
import numpy as np

from tello_lab.core.runtime import DemoRuntime
from tello_lab.ui.overlay import draw_text
from tello_lab.vision.hands import MediaPipeHandLandmarker, draw_hands

WINDOW_NAME = "tello-lab | 04_hand_landmarks"

MODEL_PATH = HAND_LANDMARKER_MODEL_PATH

RC_SPEED = 35
YAW_SPEED = 45

CONTROLS_TEXT = (
    "Controls: [t] takeoff  [l] land  [q] quit\n"
    "Manual: [w/s/a/d] move  [r/f] up/down\n"
    "Hand landmarks: show hand skeleton and index fingertip"
)


def draw_hand_landmarks_overlay(frame: np.ndarray, runtime: DemoRuntime) -> None:
    """Detect and draw hand landmarks."""
    if not hasattr(runtime, "hand_landmarker"):
        runtime.hand_landmarker = MediaPipeHandLandmarker(
            MODEL_PATH,
            num_hands=2,
            min_hand_detection_confidence=0.60,
            min_hand_presence_confidence=0.60,
            min_tracking_confidence=0.60,
        )

    hands = runtime.hand_landmarker.detect(frame)
    draw_hands(frame, hands)

    draw_text(
        frame,
        f"Hands: {len(hands)} | Model: MediaPipe Hand Landmarker",
        position=(16, 96),
        scale=0.65,
        color=(255, 255, 255),
    )

    for hand_index, hand in enumerate(hands):
        tip_x, tip_y = hand.index_finger_tip.to_pixel(frame.shape)

        cv2.circle(
            frame,
            (tip_x, tip_y),
            8,
            (0, 255, 255),
            -1,
        )

        draw_text(
            frame,
            f"{hand.handedness} index tip: x={tip_x} y={tip_y}",
            position=(16, 124 + hand_index * 28),
            scale=0.65,
            color=(255, 255, 255),
        )


def main() -> None:
    """Run a MediaPipe hand landmarks demo with manual flight controls."""
    runtime = DemoRuntime(
        window_name=WINDOW_NAME,
        controls_text=CONTROLS_TEXT,
        movement_enabled=True,
        speed=RC_SPEED,
        yaw_speed=YAW_SPEED,
    )
    runtime.run(draw_extra_overlay=draw_hand_landmarks_overlay)


if __name__ == "__main__":
    main()