from __future__ import annotations

from dataclasses import dataclass

MAX_RC_VALUE = 100


def clamp_rc(value: int) -> int:
    """Clamp a raw RC value to the Tello SDK range."""
    return max(-MAX_RC_VALUE, min(MAX_RC_VALUE, int(value)))


@dataclass(frozen=True)
class ControlCommand:
    """A Tello RC control command.

    Values follow the DJI Tello SDK convention:
    - left_right: negative = left, positive = right
    - forward_back: negative = backward, positive = forward
    - up_down: negative = down, positive = up
    - yaw: negative = rotate left, positive = rotate right
    """

    left_right: int = 0
    forward_back: int = 0
    up_down: int = 0
    yaw: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "left_right", clamp_rc(self.left_right))
        object.__setattr__(self, "forward_back", clamp_rc(self.forward_back))
        object.__setattr__(self, "up_down", clamp_rc(self.up_down))
        object.__setattr__(self, "yaw", clamp_rc(self.yaw))

    @classmethod
    def hover(cls) -> "ControlCommand":
        """Create a zero-velocity command."""
        return cls()

    @classmethod
    def left(cls, speed: int) -> "ControlCommand":
        """Create a command that moves the drone left."""
        return cls(left_right=-speed)

    @classmethod
    def right(cls, speed: int) -> "ControlCommand":
        """Create a command that moves the drone right."""
        return cls(left_right=speed)

    @classmethod
    def forward(cls, speed: int) -> "ControlCommand":
        """Create a command that moves the drone forward."""
        return cls(forward_back=speed)

    @classmethod
    def backward(cls, speed: int) -> "ControlCommand":
        """Create a command that moves the drone backward."""
        return cls(forward_back=-speed)

    @classmethod
    def up(cls, speed: int) -> "ControlCommand":
        """Create a command that moves the drone up."""
        return cls(up_down=speed)

    @classmethod
    def down(cls, speed: int) -> "ControlCommand":
        """Create a command that moves the drone down."""
        return cls(up_down=-speed)

    @classmethod
    def yaw_left(cls, speed: int) -> "ControlCommand":
        """Create a command that rotates the drone left."""
        return cls(yaw=-speed)

    @classmethod
    def yaw_right(cls, speed: int) -> "ControlCommand":
        """Create a command that rotates the drone right."""
        return cls(yaw=speed)

    @property
    def is_hover(self) -> bool:
        """Return True when all RC channels are zero."""
        return self.as_tuple() == (0, 0, 0, 0)

    def as_tuple(self) -> tuple[int, int, int, int]:
        """Return values in the order expected by send_rc_control."""
        return (self.left_right, self.forward_back, self.up_down, self.yaw)