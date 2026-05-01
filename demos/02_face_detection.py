from __future__ import annotations

import numpy as np

from tello_lab.core.runtime import DemoRuntime
from tello_lab.ui.overlay import draw_text
from tello_lab.vision.face import HaarFaceDetector, draw_faces

WINDOW_NAME = "tello-lab | 02_face_detection"

RC_SPEED = 35
YAW_SPEED = 45

CONTROLS_TEXT = (
    "Controls: [t] takeoff  [l] land  [q] quit\n"
    "Manual: [w/s/a/d] move  [r/f] up/down\n"
    "Yaw: [left/right arrows] rotate  [space] hover"
)


def draw_face_detection_overlay(frame: np.ndarray, runtime: DemoRuntime) -> None:
    """Detect and draw faces on top of the frame."""
    if not hasattr(runtime, "face_detector"):
        runtime.face_detector = HaarFaceDetector()

    faces = runtime.face_detector.detect(frame)
    draw_faces(frame, faces)

    draw_text(
        frame,
        f"Faces: {len(faces)}",
        position=(16, 96),
        scale=0.65,
        color=(255, 255, 255),
    )

    if faces:
        target = faces[0]
        center_x, center_y = target.center

        draw_text(
            frame,
            f"Target: x={center_x} y={center_y} area={target.area}",
            position=(16, 124),
            scale=0.65,
            color=(255, 255, 255),
        )


def main() -> None:
    """Run a face detection demo with manual flight controls."""
    runtime = DemoRuntime(
        window_name=WINDOW_NAME,
        controls_text=CONTROLS_TEXT,
        movement_enabled=True,
        speed=RC_SPEED,
        yaw_speed=YAW_SPEED,
    )
    runtime.run(draw_extra_overlay=draw_face_detection_overlay)


if __name__ == "__main__":
    main()