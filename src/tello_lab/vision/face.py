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
    def aspect_ratio(self) -> float:
        """Return the bounding box width-to-height ratio."""
        return self.width / self.height

    @property
    def box(self) -> tuple[int, int, int, int]:
        """Return the bounding box as x, y, width, height."""
        return (self.x, self.y, self.width, self.height)


@dataclass(frozen=True)
class FaceDetectorConfig:
    """Configuration for Haar-based face detection."""

    scale_factor: float = 1.15
    min_neighbors: int = 8
    min_face_size: tuple[int, int] = (90, 90)
    min_area_ratio: float = 0.008
    max_area_ratio: float = 0.55
    min_aspect_ratio: float = 0.65
    max_aspect_ratio: float = 1.35


class HaarFaceDetector:
    """Simple OpenCV Haar Cascade face detector with conservative filtering."""

    def __init__(self, config: FaceDetectorConfig | None = None) -> None:
        cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        self.classifier = cv2.CascadeClassifier(str(cascade_path))

        if self.classifier.empty():
            raise RuntimeError(f"Failed to load Haar cascade: {cascade_path}")

        self.config = config or FaceDetectorConfig()

    def detect(self, frame: np.ndarray) -> list[FaceDetection]:
        """Detect plausible faces in a video frame."""
        frame_height, frame_width = frame.shape[:2]
        frame_area = frame_width * frame_height

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        raw_faces = self.classifier.detectMultiScale(
            gray,
            scaleFactor=self.config.scale_factor,
            minNeighbors=self.config.min_neighbors,
            minSize=self.config.min_face_size,
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

        plausible_faces = [
            face
            for face in faces
            if self._is_plausible_face(face, frame_area=frame_area)
        ]

        return sorted(plausible_faces, key=lambda face: face.area, reverse=True)

    def _is_plausible_face(self, face: FaceDetection, *, frame_area: int) -> bool:
        area_ratio = face.area / frame_area

        if area_ratio < self.config.min_area_ratio:
            return False

        if area_ratio > self.config.max_area_ratio:
            return False

        if face.aspect_ratio < self.config.min_aspect_ratio:
            return False

        if face.aspect_ratio > self.config.max_aspect_ratio:
            return False

        return True


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