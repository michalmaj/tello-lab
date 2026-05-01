from __future__ import annotations

from typing import Any

import numpy as np
from djitellopy import Tello


class TelloDrone:
    """Small lifecycle wrapper around the DJITelloPy client."""

    def __init__(self) -> None:
        self.tello = Tello()
        self._frame_reader: Any | None = None
        self._is_streaming = False

    def connect(self) -> None:
        """Connect to the Tello drone."""
        print("Connecting to Tello...")
        self.tello.connect()

    def start_video(self) -> None:
        """Start the Tello video stream."""
        if self._is_streaming:
            return

        print("Starting video stream...")
        self.tello.streamon()
        self._frame_reader = self.tello.get_frame_read()
        self._is_streaming = True

    @property
    def frame(self) -> np.ndarray | None:
        """Return the latest video frame, if available."""
        if self._frame_reader is None:
            return None

        return self._frame_reader.frame

    def stop_video(self) -> None:
        """Stop the Tello video stream if it is running."""
        if not self._is_streaming:
            return

        try:
            self.tello.streamoff()
        except Exception:
            pass
        finally:
            self._is_streaming = False
            self._frame_reader = None

    def close(self) -> None:
        """Release drone resources."""
        self.stop_video()

        try:
            self.tello.end()
        except Exception:
            pass