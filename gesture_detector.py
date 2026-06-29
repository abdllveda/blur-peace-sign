"""
Hand gesture detection powered by MediaPipe Hands.

Designed for extension: add new gesture checks alongside is_peace_sign().
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Sequence

import cv2
import mediapipe as mp
import numpy as np

logger = logging.getLogger(__name__)


class GestureType(Enum):
    """Supported gestures. Extend this enum as new gestures are added."""

    NONE = auto()
    PEACE = auto()


# MediaPipe hand landmark indices (https://developers.google.com/mediapipe/solutions/vision/hand_landmarker)
WRIST = 0
THUMB_TIP = 4
THUMB_IP = 3
INDEX_TIP = 8
INDEX_PIP = 6
MIDDLE_TIP = 12
MIDDLE_PIP = 10
RING_TIP = 16
RING_PIP = 14
PINKY_TIP = 20
PINKY_PIP = 18


@dataclass(frozen=True)
class GestureDetectorConfig:
    """Tunable MediaPipe and gesture-matching settings."""

    max_num_hands: int = 2
    min_detection_confidence: float = 0.6
    min_tracking_confidence: float = 0.5
    # Distance ratio threshold: extended finger tip is farther from wrist than PIP.
    extension_ratio: float = 1.15
    # Thumb uses a slightly lower ratio because its range of motion differs.
    thumb_extension_ratio: float = 1.05


@dataclass(frozen=True)
class DetectionResult:
    """Outcome of processing a single frame."""

    active_gesture: GestureType
    peace_detected: bool
    num_hands: int


class GestureDetector:
    """
    Reusable MediaPipe Hands wrapper with gesture classification helpers.

    Instantiate once and call detect() per frame to avoid re-allocating models.
    """

    def __init__(self, config: Optional[GestureDetectorConfig] = None) -> None:
        self._config = config or GestureDetectorConfig()
        self._hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=self._config.max_num_hands,
            min_detection_confidence=self._config.min_detection_confidence,
            min_tracking_confidence=self._config.min_tracking_confidence,
        )
        # MediaPipe expects RGB input; conversion happens per frame in detect().

    def close(self) -> None:
        """Release MediaPipe resources."""
        self._hands.close()
        logger.info("Gesture detector closed.")

    def detect(self, bgr_frame: np.ndarray) -> DetectionResult:
        """
        Run hand tracking and classify gestures for the current frame.

        Args:
            bgr_frame: OpenCV BGR image (H, W, 3).

        Returns:
            DetectionResult with the highest-priority active gesture.
        """
        rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        # Mark array read-only where supported to avoid accidental copies downstream.
        rgb_frame.flags.writeable = False
        results = self._hands.process(rgb_frame)

        peace_detected = False
        num_hands = 0

        if results.multi_hand_landmarks and results.multi_handedness:
            num_hands = len(results.multi_hand_landmarks)

            for landmarks, handedness in zip(
                results.multi_hand_landmarks,
                results.multi_handedness,
            ):
                label = handedness.classification[0].label  # "Left" or "Right"
                if self.is_peace_sign(landmarks.landmark, label):
                    peace_detected = True
                    break

        active_gesture = GestureType.PEACE if peace_detected else GestureType.NONE

        return DetectionResult(
            active_gesture=active_gesture,
            peace_detected=peace_detected,
            num_hands=num_hands,
        )

    def is_peace_sign(self, landmarks: Sequence, handedness: str) -> bool:
        """
        Return True when index + middle fingers are extended and others are folded.

        Uses wrist-relative distances so the check remains stable across moderate
        hand rotations (not only perfectly upright palms).
        """
        wrist = landmarks[WRIST]

        index_extended = self._is_finger_extended(
            landmarks, INDEX_TIP, INDEX_PIP, wrist, self._config.extension_ratio
        )
        middle_extended = self._is_finger_extended(
            landmarks, MIDDLE_TIP, MIDDLE_PIP, wrist, self._config.extension_ratio
        )
        ring_extended = self._is_finger_extended(
            landmarks, RING_TIP, RING_PIP, wrist, self._config.extension_ratio
        )
        pinky_extended = self._is_finger_extended(
            landmarks, PINKY_TIP, PINKY_PIP, wrist, self._config.extension_ratio
        )
        thumb_extended = self._is_thumb_extended(
            landmarks, handedness, wrist, self._config.thumb_extension_ratio
        )

        return (
            index_extended
            and middle_extended
            and not ring_extended
            and not pinky_extended
            and not thumb_extended
        )

    @staticmethod
    def _distance(a, b) -> float:
        dx = a.x - b.x
        dy = a.y - b.y
        return float((dx * dx + dy * dy) ** 0.5)

    def _is_finger_extended(
        self,
        landmarks: Sequence,
        tip_idx: int,
        pip_idx: int,
        wrist,
        ratio: float,
    ) -> bool:
        tip = landmarks[tip_idx]
        pip = landmarks[pip_idx]
        tip_dist = self._distance(tip, wrist)
        pip_dist = self._distance(pip, wrist)
        if pip_dist <= 1e-6:
            return False
        return tip_dist > pip_dist * ratio

    def _is_thumb_extended(
        self,
        landmarks: Sequence,
        handedness: str,
        wrist,
        ratio: float,
    ) -> bool:
        """
        Thumb extension uses combined distance and lateral direction cues.
        """
        tip = landmarks[THUMB_TIP]
        ip = landmarks[THUMB_IP]

        distance_extended = self._is_finger_extended(
            landmarks, THUMB_TIP, THUMB_IP, wrist, ratio
        )

        # Lateral check: extended thumb points away from the palm center line.
        if handedness == "Right":
            lateral_extended = tip.x < ip.x
        else:
            lateral_extended = tip.x > ip.x

        return distance_extended and lateral_extended
