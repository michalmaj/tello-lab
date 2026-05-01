from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass(frozen=True)
class FaceDetection:
    """A detected face bounding box."""

    x: int
    y: int
    width: int
    height: int

    @property
    def area(self) -> int:
        """Return the bounding box area."""
        return self.width * self.height

    @property
    def center(self) -> tuple[int, int]:
        """Return the center point of the bounding box."""
        return (self.x + self.width // 2, self.y + self.height // 2)

    @property
    def box(self) -> tuple[int, int, int, int]:
        """Return the bounding box as x, y, width, height."""
        return (self.x, self.y, self.width, self.height)


class HaarFaceDetector:
    """Simple OpenCV Haar Cascade face detector."""

    def __init__(
        self,
        *,
        scale_factor: float = 1.1,
        min_neighbors: int = 5,
        min_face_size: tuple[int, int] = (60, 60),
    ) -> None:
        cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        self.classifier = cv2.CascadeClassifier(str(cascade_path))

        if self.classifier.empty():
            raise RuntimeError(f"Failed to load Haar cascade: {cascade_path}")

        self.scale_factor = scale_factor
        self.min_neighbors = min_neighbors
        self.min_face_size = min_face_size

    def detect(self, frame: np.ndarray) -> list[FaceDetection]:
        """Detect faces in a video frame."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        raw_faces = self.classifier.detectMultiScale(
            gray,
            scaleFactor=self.scale_factor,
            minNeighbors=self.min_neighbors,
            minSize=self.min_face_size,
        )

        faces = [
            FaceDetection(
                x=int(x),
                y=int(y),
                width=int(width),
                height=int(height),
            )
            for x, y, width, height in raw_faces
        ]

        return sorted(faces, key=lambda face: face.area, reverse=True)


def draw_faces(
    frame: np.ndarray,
    faces: list[FaceDetection],
    *,
    draw_centers: bool = True,
) -> None:
    """Draw detected faces on a video frame."""
    for index, face in enumerate(faces):
        x, y, width, height = face.box
        center_x, center_y = face.center

        color = (0, 255, 0) if index == 0 else (255, 255, 255)
        label = "target" if index == 0 else "face"

        cv2.rectangle(
            frame,
            (x, y),
            (x + width, y + height),
            color,
            2,
        )

        cv2.putText(
            frame,
            label,
            (x, max(24, y - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
            cv2.LINE_AA,
        )

        if draw_centers:
            cv2.circle(frame, (center_x, center_y), 4, color, -1)