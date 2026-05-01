from __future__ import annotations

from tello_lab.core.runtime import DemoRuntime

WINDOW_NAME = "tello-lab | 00_video_preview"
CONTROLS_TEXT = "Controls: [t] takeoff  [l] land  [q] quit"


def main() -> None:
    """Run a minimal live preview loop for the Tello drone."""
    runtime = DemoRuntime(
        window_name=WINDOW_NAME,
        controls_text=CONTROLS_TEXT,
        movement_enabled=False,
    )
    runtime.run()


if __name__ == "__main__":
    main()