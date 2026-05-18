"""
Object Detection — Projek Badar Task 99 (G3)
Deteksi wajah/objek — dinonaktifkan secara default bila privasi ketat.
Status: STUB — wire ke YOLO/DNN model lokal.

CATATAN PRIVASI: Deteksi wajah (face detection) dinonaktifkan secara default.
Aktifkan hanya jika ada kebutuhan eksplisit dan persetujuan pengguna.
"""
from __future__ import annotations

import logging

from .models import BoundingBox, DetectionResult

logger = logging.getLogger(__name__)

# Kontrol aktif/nonaktif deteksi
FACE_DETECTION_ENABLED: bool = False   # Default OFF — privasi sensitif
OBJECT_DETECTION_ENABLED: bool = True  # Default ON


def privacy_warning() -> None:
    """
    Tampilkan peringatan privasi untuk fitur face detection.
    Panggil sebelum mengaktifkan deteksi wajah.
    """
    warning = (
        "\n"
        "=" * 60 + "\n"
        "  PERINGATAN PRIVASI / PRIVACY WARNING\n"
        "=" * 60 + "\n"
        "  Deteksi wajah (face detection) memproses data biometrik\n"
        "  yang bersifat sensitif secara privasi.\n"
        "\n"
        "  Pastikan:\n"
        "  - Ada persetujuan eksplisit dari subjek gambar\n"
        "  - Sesuai regulasi privasi yang berlaku (GDPR, dll.)\n"
        "  - Hasil tidak disimpan tanpa keperluan yang jelas\n"
        "  - Fitur ini DINONAKTIFKAN secara default (FACE_DETECTION_ENABLED=False)\n"
        "=" * 60 + "\n"
    )
    print(warning)
    logger.warning("[PRIVACY] Face detection diaktifkan — pastikan kepatuhan privasi.")


def detect_objects(
    image_path: str,
    enabled: bool = OBJECT_DETECTION_ENABLED,
) -> DetectionResult:
    """
    Deteksi objek pada gambar.

    Args:
        image_path: Path ke file gambar.
        enabled: Aktifkan deteksi. Default OBJECT_DETECTION_ENABLED (True).

    Returns:
        DetectionResult berisi daftar objek yang terdeteksi.

    Notes:
        # TODO: load YOLO model, run inference. Contoh:
        #   from ultralytics import YOLO
        #   model = YOLO("yolov8n.pt")  # model lokal
        #   results = model(image_path)
        #   for box in results[0].boxes:
        #       bbox = BoundingBox(x=int(box.xyxy[0][0]), y=int(box.xyxy[0][1]),
        #                          width=int(box.xyxy[0][2]-box.xyxy[0][0]),
        #                          height=int(box.xyxy[0][3]-box.xyxy[0][1]),
        #                          label=model.names[int(box.cls)],
        #                          confidence=float(box.conf))
        # Alternatif: OpenCV DNN dengan model YOLO weights lokal
    """
    if not enabled:
        logger.info("[Detection] Deteksi objek dinonaktifkan untuk '%s'.", image_path)
        return DetectionResult(objects=[], count=0, model="disabled")

    # TODO: load YOLO model, run inference
    logger.warning(
        "[STUB] detect_objects: model YOLO belum terpasang untuk '%s'. "
        "Mengembalikan hasil kosong.",
        image_path,
    )
    return DetectionResult(objects=[], count=0, model="stub")


def detect_faces(
    image_path: str,
    enabled: bool = FACE_DETECTION_ENABLED,
) -> DetectionResult:
    """
    Deteksi wajah pada gambar.

    DINONAKTIFKAN secara default karena alasan privasi.
    Aktifkan dengan enabled=True hanya jika ada persetujuan eksplisit.

    Args:
        image_path: Path ke file gambar.
        enabled: Aktifkan deteksi wajah. Default FACE_DETECTION_ENABLED (False).

    Returns:
        DetectionResult berisi daftar wajah yang terdeteksi,
        atau model='disabled-privacy' jika nonaktif.

    Notes:
        # TODO: wire ke face detection model lokal jika diaktifkan:
        #   - OpenCV Haar Cascade (ringan, akurasi sedang)
        #   - RetinaFace / InsightFace (akurasi tinggi, lebih berat)
        #   - MediaPipe Face Detection (Google, OSS, bisa offline)
    """
    if not enabled:
        logger.info(
            "[Detection] Deteksi wajah dinonaktifkan (privasi) untuk '%s'. "
            "Set enabled=True untuk mengaktifkan.",
            image_path,
        )
        return DetectionResult(objects=[], count=0, model="disabled-privacy")

    # Tampilkan peringatan privasi saat pertama kali diaktifkan
    privacy_warning()

    # TODO: load face detection model, run inference
    logger.warning(
        "[STUB] detect_faces: model face detection belum terpasang untuk '%s'.",
        image_path,
    )
    return DetectionResult(objects=[], count=0, model="stub")
