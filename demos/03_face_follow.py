from __future__ import annotations

import time

import cv2
import numpy as np

from tello_lab.control.commands import ControlCommand
from tello_lab.control.pid import PIDConfig, PIDLimits
from tello_lab.control.tracker import FaceFollowConfig, FaceFollowController
from tello_lab.core.runtime import DemoRuntime
from tello_lab.ui.overlay import draw_text
from tello_lab.vision.face import HaarFaceDetector, draw_faces

WINDOW_NAME = "tello-lab | 03_face_follow"

RC_SPEED = 35
YAW_SPEED = 45

CONTROLS_TEXT = (
    "Controls: [t] takeoff  [l] land  [q] quit\n"
    "Manual override: [w/s/a/d] move  [r/f] up/down\n"
    "Auto follow: yaw + up/down + forward/back from face box"
)

FOLLOW_CONFIG = FaceFollowConfig(
    target_area_ratio=0.09,

    # Smaller deadzones make the drone react earlier.
    x_deadzone=0.07,
    y_deadzone=0.08,

    # Keep distance control unchanged.
    area_deadzone=0.30,

    enable_yaw=True,
    enable_vertical=True,
    enable_distance=True,

    # More responsive left/right rotation.
    yaw_pid=PIDConfig(
        kp=70.0,
        kd=6.0,
        output_limits=PIDLimits(-55.0, 55.0),
    ),

    # More responsive up/down movement.
    vertical_pid=PIDConfig(
        kp=45.0,
        kd=4.0,
        output_limits=PIDLimits(-40.0, 40.0),
    ),

    # Keep forward/back behavior conservative.
    distance_pid=PIDConfig(
        kp=28.0,
        kd=2.0,
        output_limits=PIDLimits(-25.0, 25.0),
    ),
)


def draw_face_follow_overlay(frame: np.ndarray, runtime: DemoRuntime) -> ControlCommand:
    """Detect the main face, draw debug info, and return an autonomous command."""
    if not hasattr(runtime, "face_detector"):
        runtime.face_detector = HaarFaceDetector()
        runtime.face_follow = FaceFollowController(FOLLOW_CONFIG)
        runtime.last_follow_update = time.monotonic()

    faces = runtime.face_detector.detect(frame)
    target = faces[0] if faces else None

    now = time.monotonic()
    dt = max(0.001, now - runtime.last_follow_update)
    runtime.last_follow_update = now

    command = runtime.face_follow.update(
        target,
        frame_shape=frame.shape,
        dt=dt,
    )

    draw_faces(frame, faces)
    draw_frame_center(frame)

    debug = runtime.face_follow.debug

    draw_text(
        frame,
        f"Faces: {len(faces)} | Follow: full",
        position=(16, 96),
        scale=0.65,
        color=(255, 255, 255),
    )

    draw_text(
        frame,
        (
            f"Error: x={debug.x_error:+.2f} "
            f"y={debug.y_error:+.2f} "
            f"area={debug.area_error:+.2f}"
        ),
        position=(16, 124),
        scale=0.65,
        color=(255, 255, 255),
    )

    draw_text(
        frame,
        (
            f"Auto RC: fb={command.forward_back:+d} "
            f"ud={command.up_down:+d} "
            f"yaw={command.yaw:+d}"
        ),
        position=(16, 152),
        scale=0.65,
        color=(255, 255, 255),
    )

    if runtime.manual_control is not None:
        draw_text(
            frame,
            f"Sent RC: {runtime.manual_control.current_command.as_tuple()}",
            position=(16, 180),
            scale=0.65,
            color=(255, 255, 255),
        )

    return command


def draw_frame_center(frame: np.ndarray) -> None:
    """Draw a small cross at the frame center."""
    height, width = frame.shape[:2]
    center = (width // 2, height // 2)

    cv2.line(frame, (center[0] - 12, center[1]), (center[0] + 12, center[1]), (255, 255, 255), 1)
    cv2.line(frame, (center[0], center[1] - 12), (center[0], center[1] + 12), (255, 255, 255), 1)


def main() -> None:
    """Run a full face follow demo with manual keyboard override."""
    runtime = DemoRuntime(
        window_name=WINDOW_NAME,
        controls_text=CONTROLS_TEXT,
        movement_enabled=True,
        speed=RC_SPEED,
        yaw_speed=YAW_SPEED,
    )
    runtime.run(draw_extra_overlay=draw_face_follow_overlay)


if __name__ == "__main__":
    main()