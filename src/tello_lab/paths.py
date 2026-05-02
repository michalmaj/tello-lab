from __future__ import annotations

from pathlib import Path


def find_project_root(start_path: Path | None = None) -> Path:
    """Find the project root directory by walking up from a start path."""
    current_path = (start_path or Path(__file__)).resolve()

    for candidate in [current_path, *current_path.parents]:
        if (candidate / "pyproject.toml").exists() and (candidate / "assets").exists():
            return candidate

    raise RuntimeError("Could not find project root directory.")


PROJECT_ROOT = find_project_root()
ASSETS_DIR = PROJECT_ROOT / "assets"
MODELS_DIR = ASSETS_DIR / "models"

HAND_LANDMARKER_MODEL_PATH = MODELS_DIR / "hand_landmarker.task"