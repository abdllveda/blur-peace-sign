"""
Webcam capture layer for macOS and other platforms.

Encapsulates OpenCV VideoCapture setup, frame reading, and cleanup with
explicit errors for missing devices, permission denial, and read failures.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Iterator, Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class CameraError(Exception):
    """Base exception for camera-related failures."""


class CameraNotFoundError(CameraError):
    """Raised when no usable camera device is available."""


class CameraPermissionError(CameraError):
    """Raised when the OS denies access to the camera (common on macOS)."""


class FrameCaptureError(CameraError):
    """Raised when an individual frame cannot be read from the device."""


@dataclass(frozen=True)
class CameraConfig:
    """Tunable camera settings."""

    device_index: int = 0
    width: int = 1280
    height: int = 720
    warmup_frames: int = 5
    max_open_retries: int = 3
    open_retry_delay_sec: float = 0.5
    mirror: bool = True



class Camera:
    """
    Context-managed wrapper around cv2.VideoCapture.

    Usage:
        with Camera() as camera:
            for frame in camera.frames():
                ...
    """

    def __init__(self, config: Optional[CameraConfig] = None) -> None:
        self._config = config or CameraConfig()
        self._capture: Optional[cv2.VideoCapture] = None

    def __enter__(self) -> "Camera":
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()

    @property
    def is_open(self) -> bool:
        return self._capture is not None and self._capture.isOpened()

    def open(self) -> None:
        """Open the webcam and validate that frames can be captured."""
        if self.is_open:
            return

        last_error: Optional[Exception] = None

        for attempt in range(1, self._config.max_open_retries + 1):
            capture = cv2.VideoCapture(self._config.device_index)
            if not capture.isOpened():
                capture.release()
                last_error = CameraNotFoundError(
                    f"Camera device index {self._config.device_index} could not be opened. "
                    "Verify that a webcam is connected."
                )
                logger.warning("Camera open attempt %s failed: device not opened.", attempt)
                time.sleep(self._config.open_retry_delay_sec)
                continue

            capture.set(cv2.CAP_PROP_FRAME_WIDTH, self._config.width)
            capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self._config.height)

            try:
                self._warmup(capture)
            except CameraPermissionError as exc:
                capture.release()
                last_error = exc
                logger.warning("Camera open attempt %s failed: permission denied.", attempt)
                time.sleep(self._config.open_retry_delay_sec)
                continue
            except FrameCaptureError as exc:
                capture.release()
                last_error = exc
                logger.warning("Camera open attempt %s failed: frame capture error.", attempt)
                time.sleep(self._config.open_retry_delay_sec)
                continue

            self._capture = capture
            logger.info(
                "Camera opened (index=%s, resolution=%sx%s).",
                self._config.device_index,
                int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            )
            return

        if isinstance(last_error, CameraPermissionError):
            raise last_error
        if last_error is not None:
            raise last_error
        raise CameraNotFoundError("Unable to open any camera device.")

    def read(self) -> np.ndarray:
        """Read a single BGR frame."""
        if not self.is_open or self._capture is None:
            raise CameraError("Camera is not open. Call open() before read().")

        ok, frame = self._capture.read()
        if not ok or frame is None or frame.size == 0:
            raise FrameCaptureError(
                "Failed to capture a frame from the webcam. "
                "The device may have been disconnected or permission revoked."
            )
        if self._config.mirror:
            frame = cv2.flip(frame, 1)
        return frame

    def frames(self) -> Iterator[np.ndarray]:
        """Yield frames until capture fails."""
        while self.is_open:
            try:
                yield self.read()
            except FrameCaptureError:
                logger.exception("Stopping frame iterator due to capture failure.")
                break

    def release(self) -> None:
        """Release the underlying VideoCapture resource."""
        if self._capture is not None:
            self._capture.release()
            self._capture = None
            logger.info("Camera released.")

    def _warmup(self, capture: cv2.VideoCapture) -> None:
        """
        Read a few frames after opening.

        On macOS, the first reads often fail until camera permission is granted,
        which helps distinguish permission issues from a missing device.
        """
        successes = 0
        failures = 0

        for _ in range(self._config.warmup_frames):
            ok, frame = capture.read()
            if ok and frame is not None and frame.size > 0:
                successes += 1
            else:
                failures += 1

        if successes == 0:
            if failures == self._config.warmup_frames:
                raise CameraPermissionError(
                    "Camera permission appears to be denied or the device is unavailable. "
                    "On macOS, grant camera access to Terminal or your IDE under "
                    "System Settings → Privacy & Security → Camera."
                )
            raise FrameCaptureError(
                "Camera opened but no valid frames were received during warmup."
            )
