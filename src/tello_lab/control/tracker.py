from __future__ import annotations

from dataclasses import dataclass, field

from tello_lab.control.commands import ControlCommand
from tello_lab.control.pid import PIDConfig, PIDController, PIDLimits
from tello_lab.vision.face import FaceDetection


@dataclass(frozen=True)
class FaceFollowConfig:
    """Configuration for full face follow control."""

    target_area_ratio: float = 0.09

    x_deadzone: float = 0.12
    y_deadzone: float = 0.14
    area_deadzone: float = 0.28

    enable_yaw: bool = True
    enable_vertical: bool = True
    enable_distance: bool = True

    yaw_pid: PIDConfig = field(
        default_factory=lambda: PIDConfig(
            kp=45.0,
            kd=4.0,
            output_limits=PIDLimits(-35.0, 35.0),
        )
    )
    vertical_pid: PIDConfig = field(
        default_factory=lambda: PIDConfig(
            kp=30.0,
            kd=3.0,
            output_limits=PIDLimits(-25.0, 25.0),
        )
    )
    distance_pid: PIDConfig = field(
        default_factory=lambda: PIDConfig(
            kp=28.0,
            kd=2.0,
            output_limits=PIDLimits(-25.0, 25.0),
        )
    )


@dataclass(frozen=True)
class FaceFollowDebug:
    """Debug values produced by the face follow controller."""

    x_error: float = 0.0
    y_error: float = 0.0
    area_error: float = 0.0
    area_ratio: float = 0.0


class FaceFollowController:
    """Convert a target face position into a Tello RC command."""

    def __init__(self, config: FaceFollowConfig | None = None) -> None:
        self.config = config or FaceFollowConfig()

        self.yaw_pid = PIDController(self.config.yaw_pid)
        self.vertical_pid = PIDController(self.config.vertical_pid)
        self.distance_pid = PIDController(self.config.distance_pid)

        self.debug = FaceFollowDebug()

    def reset(self) -> None:
        """Reset all controller state."""
        self.yaw_pid.reset()
        self.vertical_pid.reset()
        self.distance_pid.reset()
        self.debug = FaceFollowDebug()

    def update(
        self,
        target: FaceDetection | None,
        *,
        frame_shape: tuple[int, ...],
        dt: float,
    ) -> ControlCommand:
        """Return an RC command that follows the target face."""
        if target is None:
            self.reset()
            return ControlCommand.hover()

        frame_height, frame_width = frame_shape[:2]
        frame_area = frame_width * frame_height

        center_x, center_y = target.center

        x_error = (center_x - frame_width / 2) / (frame_width / 2)
        y_error = (frame_height / 2 - center_y) / (frame_height / 2)

        area_ratio = target.area / frame_area
        area_error = (self.config.target_area_ratio - area_ratio) / self.config.target_area_ratio

        self.debug = FaceFollowDebug(
            x_error=x_error,
            y_error=y_error,
            area_error=area_error,
            area_ratio=area_ratio,
        )

        yaw = self._update_axis(
            self.yaw_pid,
            x_error,
            dt=dt,
            deadzone=self.config.x_deadzone,
            enabled=self.config.enable_yaw,
        )
        up_down = self._update_axis(
            self.vertical_pid,
            y_error,
            dt=dt,
            deadzone=self.config.y_deadzone,
            enabled=self.config.enable_vertical,
        )
        forward_back = self._update_axis(
            self.distance_pid,
            area_error,
            dt=dt,
            deadzone=self.config.area_deadzone,
            enabled=self.config.enable_distance,
        )

        return ControlCommand(
            left_right=0,
            forward_back=forward_back,
            up_down=up_down,
            yaw=yaw,
        )

    def _update_axis(
        self,
        controller: PIDController,
        error: float,
        *,
        dt: float,
        deadzone: float,
        enabled: bool,
    ) -> int:
        if not enabled:
            controller.reset()
            return 0

        if abs(error) < deadzone:
            controller.reset()
            return 0

        return int(round(controller.update(error, dt=dt)))