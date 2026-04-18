# tello-lab

`tello-lab` is a modular experimentation playground for DJI Tello demos.

The goal of this repository is to provide a clean foundation for:
- live video preview
- manual flight control
- computer vision experiments
- gesture-based interaction
- tracking and follow behaviors
- reusable drone control building blocks

## Current status

This project is in an early stage.
The first milestone is a stable live preview and a minimal manual control loop.

## Project structure

```text
.
├── assets/
├── configs/
├── demos/
├── recordings/
├── src/
│   └── tello_lab/
└── tests/
```

## Requirements

- Python 3.11+
- A DJI Tello drone
- A Wi-Fi connection to the drone
- macOS, Linux, or Windows with OpenCV support

## Installation

Create and activate your environment, then install the project in editable mode:

```bash
pip install -e .
```

You can also install optional extras later:

```bash
pip install -e ".[vision]"
pip install -e ".[yolo]"
pip install -e ".[dev]"
```

## First demo

Run the basic video preview:

```bash
python demos/00_video_preview.py
```

### Controls

- `t` → take off
- `l` → land
- `q` → quit the preview loop

The preview overlay displays the battery percentage and current flight state.

## Safety notes

- Fly in an open indoor area.
- Keep the drone within line of sight.
- Make sure the propellers are unobstructed.
- Only take off with enough free space around the drone.
- Land immediately if the video feed freezes or control becomes unstable.

## Roadmap

- [x] Basic project structure
- [x] Live video preview
- [x] Minimal takeoff / land controls
- [ ] Keyboard flight control
- [ ] Face detection
- [ ] Face follow
- [ ] Hand landmarks
- [ ] Gesture control
- [ ] Object tracking
- [ ] Selfie mode

## License

MIT
