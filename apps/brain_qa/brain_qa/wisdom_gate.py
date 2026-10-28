"""
wisdom_gate.py — Komponen "Berpikir Sebelum Bertindak" untuk Otak SIDIX.
Mengimplementasikan prinsip kehati-hatian, analisis konteks, metode cermin, 
serta kecerdasan emosional (Respect, Empathy, Suppleness).
"""

from __future__ import annotations
import logging
from typing import Any, Dict, List, Tuple

logger = logging.getLogger("sidix.wisdom")

class WisdomGate:
    """
    Gatekeepers untuk memastikan SIDIX tidak gegabah sebelum mengambil keputusan penting.
    Terinspirasi oleh Prinsip Pareto (80/20) dan Etika "Metode Cermin".
    """

    @staticmethod
    def evaluate_intent(question: str, proposed_action: str, context: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Mengevaluasi apakah sebuah tindakan 'layak' dilakukan atau butuh 'berpikir seribu kali'.
        Returns (is_safe, suggestion).
        """
        
        # 1. Prinsip 80/20: Cek apakah konteks sudah cukup kuat (20% planning)
        if len(question.strip()) < 10 and not context.get("history"):
            return False, "Konteks terlalu tipis. Gunakan Socratic Probe untuk meminta klarifikasi."

        # 2. Metode Cermin: Simulasi dampak (Heuristik)
        harmful_keywords = ["hapus", "delete", "rm -rf", "format", "shutdown", "kill"]
        if any(k in proposed_action.lower() for k in harmful_keywords):
            # Jika tindakan bersifat destruktif, tahan diri.
            return False, "Tindakan bersifat destruktif detected. Perlu verifikasi fakta dua kali."

        # 3. Kendalikan Diri: Deteksi 'gegabah' (terlalu cepat menyimpulkan pada topik berat)
        complex_topics = ["hukum", "agama", "keuangan", "medis", "keamanan"]
        if any(t in question.lower() for t in complex_topics):
            if context.get("step_count", 0) < 1:
                return False, "Topik sensitif terdeteksi. Jangan menyimpulkan di langkah pertama. Cari sanad/referensi."

        return True, "Tindakan dinilai bijaksana. Lanjutkan."

    @staticmethod
    def apply_pareto_filter(search_results: List[Any]) -> List[Any]:
        """
        Mengambil 20% sumber paling relevan yang memberikan 80% dampak informasi.
        Menghindari 'noise' yang menghambat pertumbuhan.
        """
        if not search_results:
            return []
            
        # Urutkan berdasarkan score/sanad_tier (asumsi sudah ada)
        # Ambil top 20% (minimal 2)
        top_k = max(2, int(len(search_results) * 0.2))
        return search_results[:top_k]

def pre_action_reflection(session_id: str, thought: str, action: str):
    """
    Hook yang dipanggil oleh agent_react sebelum mengeksekusi call_tool.
    """
    logger.info(f"[{session_id}] Pre-Action Reflection: SIDIX sedang menimbang '{action}'...")
    # Implementasi logika refleksi di sini
    pass

class RelevanceScorer:
    """
    Menghitung skor relevansi terhadap aksi, tindakan, dan jawaban.
    Berdasarkan pendekatan teknis vs kreatif serta suhu emosional.
    """

    @staticmethod
    def calculate_relevance(intent: str, mode: str, emotion_level: float) -> float:
        """
        Menghitung skor relevansi (0.0 - 1.0).
        intent: 'technical' atau 'creative'
        mode: 'fix-it' atau 'mirroring'
        emotion_level: 0.0 (datar) - 1.0 (sangat emosional)
        """
        score = 0.5
        
        # 1. Jika mode teknis tapi banyak 'basa-basi' emosional (low relevance)
        if intent == "technical" and mode == "mirroring":
            score -= 0.2
            
        # 2. Jika mode kreatif tapi langsung memberi saran/fix (Advice Trap detect)
        if intent == "creative" and mode == "fix-it":
            score -= 0.3
            
        # 3. Kesesuaian emosi dengan keluwesan (Suppleness)
        if emotion_level > 0.7 and mode == "mirroring":
            score += 0.4
            
        return min(1.0, max(0.0, score))

    @staticmethod
    def detect_advice_trap(answer: str) -> bool:
        """Deteksi apakah jawaban terlalu menggurui (bossy)."""
        bossy_markers = ["kamu harus", "sebaiknya kamu", "kamu perlu", "saya sarankan"]
        return any(m in answer.lower() for m in bossy_markers)
