from __future__ import annotations

import pytest

from tello_lab.control.pid import PIDConfig, PIDController, PIDLimits


def test_pid_returns_proportional_output() -> None:
    controller = PIDController(
        PIDConfig(
            kp=2.0,
            output_limits=PIDLimits(-100.0, 100.0),
        )
    )

    assert controller.update(10.0, dt=1.0) == 20.0


def test_pid_clamps_output_to_limits() -> None:
    controller = PIDController(
        PIDConfig(
            kp=10.0,
            output_limits=PIDLimits(-50.0, 50.0),
        )
    )

    assert controller.update(10.0, dt=1.0) == 50.0
    assert controller.update(-10.0, dt=1.0) == -50.0


def test_pid_accumulates_integral_term() -> None:
    controller = PIDController(
        PIDConfig(
            kp=0.0,
            ki=2.0,
            output_limits=PIDLimits(-100.0, 100.0),
            integral_limits=PIDLimits(-100.0, 100.0),
        )
    )

    assert controller.update(5.0, dt=1.0) == 10.0
    assert controller.update(5.0, dt=1.0) == 20.0


def test_pid_clamps_integral_state() -> None:
    controller = PIDController(
        PIDConfig(
            kp=0.0,
            ki=1.0,
            output_limits=PIDLimits(-100.0, 100.0),
            integral_limits=PIDLimits(-10.0, 10.0),
        )
    )

    assert controller.update(100.0, dt=1.0) == 10.0
    assert controller.integral == 10.0


def test_pid_uses_derivative_after_first_update() -> None:
    controller = PIDController(
        PIDConfig(
            kp=0.0,
            kd=1.0,
            output_limits=PIDLimits(-100.0, 100.0),
        )
    )

    assert controller.update(10.0, dt=1.0) == 0.0
    assert controller.update(15.0, dt=1.0) == 5.0


def test_pid_reset_clears_state() -> None:
    controller = PIDController(
        PIDConfig(
            kp=1.0,
            ki=1.0,
            output_limits=PIDLimits(-100.0, 100.0),
        )
    )

    controller.update(10.0, dt=1.0)
    controller.reset()

    assert controller.integral == 0.0
    assert controller.previous_error is None


def test_pid_rejects_non_positive_dt() -> None:
    controller = PIDController(PIDConfig(kp=1.0))

    with pytest.raises(ValueError, match="dt must be greater than zero"):
        controller.update(10.0, dt=0.0)