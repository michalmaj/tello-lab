from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from tello_lab.control.commands import ControlCommand
from tello_lab.control.keyboard import KeyboardAction, read_keyboard_input


@dataclass(frozen=True)
class ManualControlUpdate:
    """A single manual control update produced by keyboard input."""

    action: KeyboardAction = KeyboardAction.NONE
    command: ControlCommand | None = None
    should_quit: bool = False
    used_manual_command: bool = False


class ManualFlightController:
    """Shared manual flight controller for Tello demos.

    Manual keyboard commands always have priority over autonomous commands.
    """

    def __init__(
        self,
        tello: Any,
        *,
        movement_enabled: bool = True,
        speed: int = 35,
        yaw_speed: int = 45,
        command_timeout_seconds: float = 0.35,
        rc_send_interval_seconds: float = 0.05,
    ) -> None:
        self.tello = tello
        self.movement_enabled = movement_enabled
        self.speed = speed
        self.yaw_speed = yaw_speed
        self.command_timeout_seconds = command_timeout_seconds
        self.rc_send_interval_seconds = rc_send_interval_seconds

        self.is_flying = False
        self.current_command = ControlCommand.hover()

        now = time.monotonic()
        self._last_command_update = now
        self._last_rc_send = 0.0

    def tick(self, autonomous_command: ControlCommand | None = None) -> ManualControlUpdate:
        """Process keyboard input, autonomous command, and send RC commands."""
        now = time.monotonic()

        keyboard_input = read_keyboard_input(
            speed=self.speed,
            yaw_speed=self.yaw_speed,
        )

        should_quit = False
        used_manual_command = False

        if keyboard_input.action == KeyboardAction.TAKEOFF:
            self.takeoff()

        elif keyboard_input.action == KeyboardAction.LAND:
            self.land()

        elif keyboard_input.action == KeyboardAction.QUIT:
            should_quit = True
            self.land()

        if self.movement_enabled and keyboard_input.command is not None:
            self.current_command = keyboard_input.command
            self._last_command_update = now
            used_manual_command = True

        elif autonomous_command is not None and self.is_flying:
            self.current_command = autonomous_command
            self._last_command_update = now

        self._apply_command_timeout(now)
        self._send_current_command_if_needed(now)

        return ManualControlUpdate(
            action=keyboard_input.action,
            command=keyboard_input.command,
            should_quit=should_quit,
            used_manual_command=used_manual_command,
        )

    def takeoff(self) -> None:
        """Take off if the drone is not already flying."""
        if self.is_flying:
            return

        print("Takeoff...")
        self.tello.takeoff()
        self.is_flying = True
        self.current_command = ControlCommand.hover()
        self._last_command_update = time.monotonic()

    def land(self) -> None:
        """Land if the drone is currently flying."""
        if not self.is_flying:
            return

        try:
            print("Landing...")
            self.current_command = ControlCommand.hover()
            self.tello.send_rc_control(0, 0, 0, 0)
            self.tello.land()
        except Exception as error:
            print(f"Landing failed: {error}")
        finally:
            self.is_flying = False
            self.current_command = ControlCommand.hover()

    def shutdown(self) -> None:
        """Safely stop manual control and land if needed."""
        self.land()

    def _apply_command_timeout(self, now: float) -> None:
        if now - self._last_command_update > self.command_timeout_seconds:
            self.current_command = ControlCommand.hover()

    def _send_current_command_if_needed(self, now: float) -> None:
        if not self.is_flying:
            return

        if now - self._last_rc_send < self.rc_send_interval_seconds:
            return

        self.tello.send_rc_control(*self.current_command.as_tuple())
        self._last_rc_send = now