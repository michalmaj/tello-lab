from __future__ import annotations

import time

import cv2
from djitellopy import Tello

WINDOW_NAME = "tello-lab | 00_video_preview"
BATTERY_REFRESH_SECONDS = 2.0


def draw_overlay(frame, battery: int | None, is_flying: bool) -> None:
    """Draw the demo HUD on top of the current frame."""
    status_text = "FLYING" if is_flying else "READY"
    battery_text = f"Battery: {battery}%" if battery is not None else "Battery: N/A"

    cv2.putText(
        frame,
        battery_text,
        (16, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        f"State: {status_text}",
        (16, 64),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        "Controls: [t] takeoff  [l] land  [q] quit",
        (16, frame.shape[0] - 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )


def main() -> None:
    """Run a minimal live preview loop for the Tello drone."""
    tello = Tello()
    frame_read = None
    is_flying = False
    battery: int | None = None
    last_battery_refresh = 0.0

    try:
        print("Connecting to Tello...")
        tello.connect()

        battery = tello.get_battery()
        print(f"Connected. Battery: {battery}%")

        print("Starting video stream...")
        tello.streamon()
        frame_read = tello.get_frame_read()

        while True:
            frame = frame_read.frame

            if frame is None:
                time.sleep(0.01)
                continue

            now = time.monotonic()
            if now - last_battery_refresh >= BATTERY_REFRESH_SECONDS:
                try:
                    battery = tello.get_battery()
                except Exception:
                    pass
                last_battery_refresh = now

            display_frame = frame.copy()
            draw_overlay(display_frame, battery=battery, is_flying=is_flying)
            cv2.imshow(WINDOW_NAME, display_frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("t"):
                if not is_flying:
                    print("Takeoff...")
                    tello.takeoff()
                    is_flying = True

            elif key == ord("l"):
                if is_flying:
                    print("Landing...")
                    tello.land()
                    is_flying = False

            elif key == ord("q"):
                if is_flying:
                    print("Landing before exit...")
                    tello.land()
                    is_flying = False
                print("Exiting preview loop.")
                break

    except KeyboardInterrupt:
        print("Interrupted by user.")
        if is_flying:
            try:
                print("Landing after keyboard interrupt...")
                tello.land()
            except Exception:
                pass

    finally:
        cv2.destroyAllWindows()

        try:
            tello.streamoff()
        except Exception:
            pass

        try:
            tello.end()
        except Exception:
            pass


if __name__ == "__main__":
    main()