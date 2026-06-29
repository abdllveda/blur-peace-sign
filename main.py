"""
Real-time peace-sign gesture blur application.

Press Q in the preview window to exit cleanly.
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass

import cv2
import numpy as np

from camera import (
    Camera,
    CameraError,
    CameraNotFoundError,
    CameraPermissionError,
    FrameCaptureError,
)
from gesture_detector import GestureDetector, GestureType

logger = logging.getLogger(__name__)

WINDOW_NAME = "Foto Kita Blur"
QUIT_KEY = ord("q")

# Gaussian blur strength (must be odd). Tune for stronger/weaker blur.
BLUR_KERNEL_SIZE = (51, 51)
BLUR_SIGMA = 0  # 0 lets OpenCV derive sigma from kernel size.


@dataclass(frozen=True)
class AppConfig:
    """Top-level runtime settings."""

    blur_kernel_size: tuple[int, int] = BLUR_KERNEL_SIZE
    blur_sigma: float = BLUR_SIGMA


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )


def apply_blur(frame: np.ndarray, kernel_size: tuple[int, int], sigma: float) -> np.ndarray:
    """Apply Gaussian blur to the entire frame."""
    return cv2.GaussianBlur(frame, kernel_size, sigma)



def run_app(config: AppConfig | None = None) -> int:
    """
    Main event loop: capture frames, detect gestures, blur on peace sign.

    Returns:
        Process exit code (0 success, non-zero on fatal startup errors).
    """
    app_config = config or AppConfig()
    detector = GestureDetector()

    try:
        with Camera() as camera:
            cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

            while True:
                try:
                    frame = camera.read()
                except FrameCaptureError as exc:
                    logger.error("%s", exc)
                    break

                result = detector.detect(frame)
                peace_active = result.active_gesture == GestureType.PEACE

                display_frame = (
                    apply_blur(frame, app_config.blur_kernel_size, app_config.blur_sigma)
                    if peace_active
                    else frame
                )



                cv2.imshow(WINDOW_NAME, display_frame)

                key = cv2.waitKey(1) & 0xFF
                if key == QUIT_KEY:
                    logger.info("Quit key pressed. Exiting.")
                    break

    except CameraPermissionError as exc:
        logger.error("%s", exc)
        return 1
    except CameraNotFoundError as exc:
        logger.error("%s", exc)
        return 1
    except CameraError as exc:
        logger.error("Camera error: %s", exc)
        return 1
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
    finally:
        detector.close()
        cv2.destroyAllWindows()

    return 0


def main() -> None:
    configure_logging()
    sys.exit(run_app())


if __name__ == "__main__":
    main()
