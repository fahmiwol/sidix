# -*- coding: utf-8 -*-
"""
Pose Estimation — Projek Badar Task 107 (G3, opsional)
Surah Al-Mursalat (#77) — Tambahkan satu bukti untuk keputusan produk.

Estimasi pose manusia pada gambar. DIMATIKAN secara default.
Status: STUB — aktifkan hanya bila stack mendukung dan ada kebutuhan eksplisit.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Kontrol aktif/nonaktif
# ---------------------------------------------------------------------------

POSE_ESTIMATION_ENABLED: bool = False
"""Pose estimation dimatikan secara default. Set True secara eksplisit bila diperlukan."""


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@dataclass
class Keypoint:
    """Satu titik keypoint pada tubuh manusia."""
    name: str           # "nose", "left_shoulder", dll.
    x: float
    y: float
    confidence: float = 0.0
    visible: bool = True


@dataclass
class PersonPose:
    """Pose satu orang dalam gambar."""
    person_id: int
    keypoints: list[Keypoint] = field(default_factory=list)
    bounding_box: dict = field(default_factory=dict)
    overall_confidence: float = 0.0


@dataclass
class PoseResult:
    """Hasil estimasi pose dari satu gambar."""
    image_path: str
    persons: list[PersonPose] = field(default_factory=list)
    person_count: int = 0
    model: str = "stub"
    enabled: bool = False
    error: str | None = None


# ---------------------------------------------------------------------------
# Standard COCO keypoints (17 titik)
# ---------------------------------------------------------------------------

COCO_KEYPOINTS = [
    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle",
]


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def estimate_pose(
    image_path: str,
    enabled: bool = POSE_ESTIMATION_ENABLED,
    min_confidence: float = 0.5,
) -> PoseResult:
    """
    Estimasi pose manusia pada gambar.

    Args:
        image_path: Path ke file gambar.
        enabled: Override kontrol global. False = langsung kembalikan stub disabled.
        min_confidence: Threshold confidence minimum per keypoint.

    Returns:
        PoseResult. Bila tidak aktif, person_count=0 dan enabled=False.

    TODO: Wire ke model pose lokal:
        - MediaPipe Pose (Google, CPU-friendly)
        - YOLOv8-pose (Ultralytics)
        - MMPose (OpenMMLab)
        Install: pip install mediapipe  ATAU  pip install ultralytics
    """
    if not enabled:
        logger.info(
            "[POSE] Pose estimation dinonaktifkan (POSE_ESTIMATION_ENABLED=False). "
            "Set enabled=True untuk mengaktifkan."
        )
        return PoseResult(
            image_path=image_path,
            persons=[],
            person_count=0,
            model="disabled",
            enabled=False,
        )

    # TODO: Implementasi nyata di sini
    logger.warning(
        "[STUB] pose_estimation.estimate_pose() — model tidak dimuat. "
        "Wire ke MediaPipe atau YOLOv8-pose."
    )
    return PoseResult(
        image_path=image_path,
        persons=[],
        person_count=0,
        model="stub",
        enabled=True,
        error="Pose model not loaded. Install mediapipe: pip install mediapipe",
    )


def keypoints_to_dict(pose: PersonPose) -> dict:
    """Konversi PersonPose ke dict yang mudah di-serialize."""
    return {
        "person_id": pose.person_id,
        "overall_confidence": pose.overall_confidence,
        "bounding_box": pose.bounding_box,
        "keypoints": {
            kp.name: {
                "x": kp.x,
                "y": kp.y,
                "confidence": kp.confidence,
                "visible": kp.visible,
            }
            for kp in pose.keypoints
        },
    }
