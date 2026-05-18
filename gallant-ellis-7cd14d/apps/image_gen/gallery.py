"""
Gallery — Projek Badar Task 86 (G2)
Gallery hasil + penghapusan massal.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_GALLERY_LOG_PATH = Path(".data/image_gen/gallery.jsonl")


@dataclass
class GalleryItem:
    """Satu entri di galeri gambar."""

    item_id: str
    image_path: str
    thumbnail_path: Optional[str]
    prompt: str
    created_at: str
    user_id: str
    metadata: dict = field(default_factory=dict)


class Gallery:
    """
    Galeri gambar in-memory dengan persistensi ke JSONL.

    Mendukung listing, delete tunggal, dan bulk delete.
    """

    def __init__(self) -> None:
        self._items: list[GalleryItem] = []
        self.load_from_disk()

    # ------------------------------------------------------------------
    # Operasi tulis
    # ------------------------------------------------------------------

    def add(self, item: GalleryItem) -> None:
        """Tambahkan item baru ke galeri."""
        self._items.append(item)
        self.save_to_disk()
        logger.info("Gallery item ditambahkan: %s oleh user=%s", item.item_id, item.user_id)

    def delete(self, item_id: str, user_id: str) -> bool:
        """
        Hapus satu item galeri dan file gambarnya.

        Returns:
            True bila berhasil, False bila item tidak ditemukan atau bukan milik user.
        """
        for i, item in enumerate(self._items):
            if item.item_id == item_id:
                if item.user_id != user_id:
                    logger.warning(
                        "User %s mencoba menghapus item %s milik user %s.",
                        user_id, item_id, item.user_id,
                    )
                    return False
                self._items.pop(i)
                # Hapus file gambar bila ada
                self._delete_file(item.image_path)
                if item.thumbnail_path:
                    self._delete_file(item.thumbnail_path)
                self.save_to_disk()
                logger.info("Gallery item %s dihapus oleh user %s.", item_id, user_id)
                return True

        logger.warning("Gallery item %s tidak ditemukan.", item_id)
        return False

    def bulk_delete(self, item_ids: list[str], user_id: str) -> dict:
        """
        Hapus beberapa item sekaligus.

        Returns:
            dict berisi jumlah deleted dan failed.
        """
        deleted = 0
        failed = 0
        for item_id in item_ids:
            if self.delete(item_id, user_id):
                deleted += 1
            else:
                failed += 1
        logger.info(
            "Bulk delete: %d berhasil, %d gagal. user=%s", deleted, failed, user_id
        )
        return {"deleted": deleted, "failed": failed}

    # ------------------------------------------------------------------
    # Operasi baca
    # ------------------------------------------------------------------

    def list_items(
        self,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[GalleryItem]:
        """Daftar item galeri dengan filter user_id opsional dan pagination."""
        items = self._items
        if user_id is not None:
            items = [it for it in items if it.user_id == user_id]
        return items[offset : offset + limit]

    # ------------------------------------------------------------------
    # Persistensi
    # ------------------------------------------------------------------

    def load_from_disk(self) -> None:
        """Muat gallery.jsonl dari disk saat init."""
        if not _GALLERY_LOG_PATH.exists():
            return
        loaded = []
        with _GALLERY_LOG_PATH.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    loaded.append(GalleryItem(**data))
                except Exception as exc:
                    logger.warning("Gagal memuat baris gallery.jsonl: %s", exc)
        self._items = loaded
        logger.info("Gallery dimuat dari disk: %d item.", len(self._items))

    def save_to_disk(self) -> None:
        """Tulis seluruh gallery ke gallery.jsonl (overwrite)."""
        _GALLERY_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _GALLERY_LOG_PATH.open("w", encoding="utf-8") as fh:
            for item in self._items:
                fh.write(json.dumps(asdict(item), ensure_ascii=False) + "\n")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _delete_file(path: str) -> None:
        try:
            if path and os.path.exists(path):
                os.remove(path)
                logger.debug("File dihapus: %s", path)
        except OSError as exc:
            logger.warning("Gagal menghapus file %s: %s", path, exc)


# Instance global
gallery = Gallery()
