from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PIDLimits:
    """Minimum and maximum limits for a PID value."""

    minimum: float
    maximum: float

    def clamp(self, value: float) -> float:
        """Clamp a value to the configured range."""
        return max(self.minimum, min(self.maximum, value))


@dataclass(frozen=True)
class PIDConfig:
    """Configuration for a PID controller."""

    kp: float
    ki: float = 0.0
    kd: float = 0.0
    output_limits: PIDLimits = PIDLimits(-100.0, 100.0)
    integral_limits: PIDLimits = PIDLimits(-100.0, 100.0)


class PIDController:
    """A small deterministic PID controller.

    The controller works directly on error values.

    Positive error produces positive output.
    Negative error produces negative output.
    """

    def __init__(self, config: PIDConfig) -> None:
        self.config = config
        self._integral = 0.0
        self._previous_error: float | None = None

    @property
    def integral(self) -> float:
        """Return the current integral term state."""
        return self._integral

    @property
    def previous_error(self) -> float | None:
        """Return the previous error value."""
        return self._previous_error

    def reset(self) -> None:
        """Reset internal PID state."""
        self._integral = 0.0
        self._previous_error = None

    def update(self, error: float, *, dt: float) -> float:
        """Update the PID controller and return the control output."""
        if dt <= 0:
            raise ValueError("dt must be greater than zero")

        proportional = self.config.kp * error

        self._integral += error * dt
        self._integral = self.config.integral_limits.clamp(self._integral)
        integral = self.config.ki * self._integral

        derivative = 0.0
        if self._previous_error is not None:
            derivative = (error - self._previous_error) / dt

        derivative_output = self.config.kd * derivative

        self._previous_error = error

        output = proportional + integral + derivative_output
        return self.config.output_limits.clamp(output)