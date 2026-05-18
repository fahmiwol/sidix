"""
permanent_learning.py — Permanent Learning System SIDIX

Konsep inti:
  Manusia yang sudah bisa jalan tidak akan lupa cara jalan.
  Malah berkembang: jalan → lari → menari → koreografi.

Implementasi:
  - Skills yang dipelajari TIDAK pernah dihapus (hanya bisa dormant)
  - Setiap penggunaan skill → skill makin kuat (reinforcement via usage)
  - Skills bisa dikombinasikan menjadi meta-skills
  - Self-play (SPIN-style): SIDIX challenge dirinya sendiri untuk strengthen skills
  - Trajectory tracking: visual progress over time

SPIN = Self-Play via INtrospection
  Terinspirasi dari AlphaGo Zero self-play: AI bermain vs dirinya sendiri
  untuk mendapatkan feedback tanpa membutuhkan data eksternal.
"""

from __future__ import annotations

import json
import math
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────
# KONSTANTA
# ─────────────────────────────────────────────

DEFAULT_DATA_DIR = Path(".data") / "permanent_learning"

# Decay factor — skill yang lama tidak dipakai sedikit melemah (tapi tidak hilang)
# 0.99 = sangat slow decay, skill tidak akan pernah < min_strength
DECAY_RATE = 0.99
MIN_STRENGTH = 0.1  # Skill tidak bisa di bawah ini
MAX_STRENGTH = 1.0

# Reinforcement
USAGE_BOOST = 0.05   # Setiap penggunaan meningkatkan strength
SUCCESS_BOOST = 0.10  # Penggunaan sukses boost lebih besar
FAILURE_PENALTY = 0.02  # Gagal menurunkan sedikit (masih belajar)

# Self-play rounds
DEFAULT_SELF_PLAY_ROUNDS = 3

# ─────────────────────────────────────────────
# KELAS SKILL
# ─────────────────────────────────────────────

class Skill:
    """Representasi satu skill yang dipelajari."""

    def __init__(
        self,
        name: str,
        domain: str,
        description: str = "",
        strength: float = 0.3,
        tags: Optional[list] = None,
        source: str = "learned",
    ):
        self.skill_id = hashlib.md5(f"{name}:{domain}".encode()).hexdigest()[:12]
        self.name = name
        self.domain = domain
        self.description = description
        self.strength = max(MIN_STRENGTH, min(MAX_STRENGTH, strength))
        self.tags = tags or []
        self.source = source
        self.created_at = datetime.now().isoformat()
        self.last_used = datetime.now().isoformat()
        self.usage_count = 0
        self.success_count = 0
        self.fail_count = 0
        self.usage_history: list[dict] = []
        self.is_dormant = False
        self.combined_from: list[str] = []  # skill_ids jika ini meta-skill

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, d: dict) -> "Skill":
        s = cls.__new__(cls)
        s.__dict__.update(d)
        return s

    def reinforce(self, success: bool = True, context: str = "") -> float:
        """Perkuat skill berdasarkan penggunaan. Return strength baru."""
        boost = SUCCESS_BOOST if success else -FAILURE_PENALTY
        old_strength = self.strength
        self.strength = max(MIN_STRENGTH, min(MAX_STRENGTH, self.strength + boost))
        self.usage_count += 1
        self.last_used = datetime.now().isoformat()
        if success:
            self.success_count += 1
        else:
            self.fail_count += 1

        self.usage_history.append({
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "context": context[:100],
            "strength_before": round(old_strength, 3),
            "strength_after": round(self.strength, 3),
        })

        # Keep history manageable
        if len(self.usage_history) > 100:
            self.usage_history = self.usage_history[-100:]

        return self.strength

    def apply_decay(self, days_since_use: float) -> None:
        """Apply time decay — skill melemah perlahan jika tidak dipakai."""
        if days_since_use > 7:  # Decay mulai setelah 1 minggu tidak dipakai
            decay = DECAY_RATE ** (days_since_use - 7)
            self.strength = max(MIN_STRENGTH, self.strength * decay)

    def get_level(self) -> str:
        """Dapatkan label level berdasarkan strength."""
        if self.strength >= 0.9:
            return "maestro"
        elif self.strength >= 0.75:
            return "expert"
        elif self.strength >= 0.55:
            return "proficient"
        elif self.strength >= 0.35:
            return "developing"
        else:
            return "beginner"


# ─────────────────────────────────────────────
# KELAS UTAMA
# ─────────────────────────────────────────────

class PermanentLearning:
    """
    Sistem Pembelajaran Permanen SIDIX.

    Setiap skill yang masuk tidak pernah hilang — hanya bisa dormant jika
    sangat lama tidak dipakai, dan bisa diaktifkan kembali.

    Analogi: manusia tidak lupa cara berjalan meski sudah 10 tahun tidak berjalan.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._skills: dict[str, Skill] = {}
        self._load_skills()

    # ─── SKILL MANAGEMENT ───

    def add_skill(
        self,
        name: str,
        domain: str,
        description: str = "",
        initial_strength: float = 0.3,
        tags: Optional[list] = None,
        source: str = "learned",
    ) -> dict:
        """
        Tambahkan skill baru. Jika sudah ada, reinforce yang ada.

        Returns:
            dict info skill
        """
        skill_id = hashlib.md5(f"{name}:{domain}".encode()).hexdigest()[:12]

        if skill_id in self._skills:
            # Skill sudah ada — reinforce dan aktifkan kembali jika dormant
            skill = self._skills[skill_id]
            skill.is_dormant = False
            skill.reinforce(success=True, context=f"Re-learned: {name}")
            action = "reinforced"
        else:
            skill = Skill(
                name=name,
                domain=domain,
                description=description,
                strength=initial_strength,
                tags=tags or [],
                source=source,
            )
            self._skills[skill_id] = skill
            action = "added"

        self._save_skills()

        return {
            "action": action,
            "skill_id": skill.skill_id,
            "name": skill.name,
            "domain": skill.domain,
            "strength": round(skill.strength, 3),
            "level": skill.get_level(),
        }

    def reinforce_skill(self, skill_name: str, usage_context: dict) -> dict:
        """
        Reinforce skill yang sudah ada berdasarkan penggunaan.

        Args:
            skill_name: nama skill
            usage_context: dict dengan keys 'success' (bool), 'description' (str), 'domain' (str)

        Returns:
            dict status reinforcement
        """
        # Cari skill berdasarkan nama
        matching = [
            s for s in self._skills.values()
            if s.name.lower() == skill_name.lower()
        ]

        if not matching:
            # Auto-create skill baru
            domain = usage_context.get("domain", "general")
            result = self.add_skill(skill_name, domain, source="auto_reinforced")
            return {**result, "note": "Skill baru dibuat dari reinforcement"}

        skill = matching[0]
        success = usage_context.get("success", True)
        context_str = usage_context.get("description", "")

        old_strength = skill.strength
        new_strength = skill.reinforce(success=success, context=context_str)

        self._save_skills()

        return {
            "skill_id": skill.skill_id,
            "skill_name": skill.name,
            "success": success,
            "strength_before": round(old_strength, 3),
            "strength_after": round(new_strength, 3),
            "delta": round(new_strength - old_strength, 3),
            "level": skill.get_level(),
            "usage_count": skill.usage_count,
            "message": f"Skill '{skill.name}' {'diperkuat' if success else 'mengalami setback tapi tetap ada'}",
        }

    def combine_skills(self, skill_names: list[str]) -> dict:
        """
        Gabungkan beberapa skill menjadi meta-skill baru.

        Contoh: "python" + "machine_learning" + "data_viz" → "data_scientist"

        Args:
            skill_names: list nama skill yang akan digabung

        Returns:
            dict info meta-skill baru
        """
        if len(skill_names) < 2:
            return {"error": "Butuh minimal 2 skill untuk membuat meta-skill"}

        # Cari skill yang ada
        found_skills = []
        missing = []
        for name in skill_names:
            matches = [s for s in self._skills.values() if s.name.lower() == name.lower()]
            if matches:
                found_skills.append(matches[0])
            else:
                missing.append(name)

        if len(found_skills) < 2:
            return {
                "error": f"Hanya ditemukan {len(found_skills)} skill dari {len(skill_names)} yang diminta",
                "missing": missing,
            }

        # Strength meta-skill = geometric mean dari skills komponen
        strengths = [s.strength for s in found_skills]
        meta_strength = math.exp(sum(math.log(s) for s in strengths) / len(strengths))

        # Nama meta-skill otomatis
        domains = list({s.domain for s in found_skills})
        meta_name = " × ".join(s.name for s in found_skills)
        meta_domain = " + ".join(domains[:3])

        # Buat meta-skill
        meta_skill = Skill(
            name=meta_name,
            domain=meta_domain,
            description=f"Meta-skill gabungan dari: {', '.join(s.name for s in found_skills)}",
            strength=meta_strength * 0.8,  # Sedikit lebih lemah dari components
            tags=[f"meta-skill"] + [s.name for s in found_skills],
            source="combined",
        )
        meta_skill.combined_from = [s.skill_id for s in found_skills]

        self._skills[meta_skill.skill_id] = meta_skill
        self._save_skills()

        return {
            "meta_skill_id": meta_skill.skill_id,
            "meta_skill_name": meta_name,
            "components": [s.name for s in found_skills],
            "strength": round(meta_skill.strength, 3),
            "level": meta_skill.get_level(),
            "missing_components": missing,
            "note": (
                f"Meta-skill dibuat dengan strength {meta_skill.strength:.2f} "
                f"(geometric mean dari {[round(s,2) for s in strengths]})"
            ),
        }

    # ─── SELF-PLAY (SPIN) ───

    def self_play(self, skill_name: str, n_rounds: int = DEFAULT_SELF_PLAY_ROUNDS) -> list[dict]:
        """
        SPIN-style self-play untuk memperkuat skill.

        SIDIX challenge dirinya sendiri: buat soal → jawab → evaluasi → reinforce.

        Terinspirasi dari:
        - AlphaGo Zero: self-play tanpa data manusia
        - SPIN paper: Self-Play fINe-tuning — LLM generates Q, answers Q, learns from gap

        Args:
            skill_name: nama skill yang ingin di-self-play
            n_rounds: jumlah ronde self-play

        Returns:
            list of dict hasil setiap ronde
        """
        # Cari skill
        matching = [s for s in self._skills.values() if s.name.lower() == skill_name.lower()]
        if not matching:
            return [{"error": f"Skill '{skill_name}' tidak ditemukan. Tambahkan dulu dengan add_skill()"}]

        skill = matching[0]
        rounds_results = []

        # Challenge templates berdasarkan level
        challenge_templates = self._get_challenge_templates(skill.get_level(), skill.domain)

        for i in range(n_rounds):
            # Select challenge
            challenge_idx = i % len(challenge_templates)
            challenge = challenge_templates[challenge_idx]

            # Simulate attempt (dalam real SIDIX, ini akan trigger actual LLM reasoning)
            attempt_quality = self._simulate_attempt(skill.strength, challenge["difficulty"])

            success = attempt_quality >= 0.6
            delta = skill.reinforce(success=success, context=f"Self-play round {i+1}: {challenge['type']}")

            round_result = {
                "round": i + 1,
                "skill": skill.name,
                "challenge_type": challenge["type"],
                "challenge": challenge["description"].format(skill=skill.name),
                "difficulty": challenge["difficulty"],
                "attempt_quality": round(attempt_quality, 3),
                "success": success,
                "strength_after": round(skill.strength, 3),
                "level": skill.get_level(),
                "feedback": self._generate_feedback(attempt_quality, challenge),
                "next_challenge": (
                    "Tingkatkan difficulty" if success
                    else "Coba challenge yang sama atau lebih mudah"
                ),
            }
            rounds_results.append(round_result)

        self._save_skills()

        # Summary
        initial_strength = rounds_results[0]["strength_after"] - (
            SUCCESS_BOOST if rounds_results[0]["success"] else -FAILURE_PENALTY
        )
        final_strength = rounds_results[-1]["strength_after"]
        improvement = round(final_strength - initial_strength, 3)

        rounds_results.append({
            "round": "summary",
            "skill": skill.name,
            "rounds_completed": n_rounds,
            "initial_strength": round(initial_strength, 3),
            "final_strength": round(final_strength, 3),
            "improvement": improvement,
            "success_rate": f"{sum(1 for r in rounds_results[:-1] if r['success'])}/{n_rounds}",
            "conclusion": (
                f"Self-play {n_rounds} ronde {'meningkatkan' if improvement > 0 else 'mempertahankan'} "
                f"skill '{skill_name}' dari {initial_strength:.2f} → {final_strength:.2f}"
            ),
        })

        return rounds_results

    # ─── QUERY & ANALYTICS ───

    def get_skill_strength(self, skill_name: str) -> float:
        """
        Dapatkan strength skill.

        Returns:
            float 0.0-1.0, atau -1 jika tidak ditemukan
        """
        matching = [s for s in self._skills.values() if s.name.lower() == skill_name.lower()]
        if not matching:
            return -1.0
        return round(matching[0].strength, 3)

    def get_all_skills(self, domain_filter: Optional[str] = None) -> list[dict]:
        """
        Dapatkan semua skill, optional filter by domain.

        Returns:
            list of dict skill info
        """
        skills = list(self._skills.values())

        if domain_filter:
            skills = [s for s in skills if domain_filter.lower() in s.domain.lower()]

        # Apply decay before returning
        now = datetime.now()
        for skill in skills:
            try:
                last_used_dt = datetime.fromisoformat(skill.last_used)
                days_since = (now - last_used_dt).days
                skill.apply_decay(days_since)
            except Exception:
                pass

        # Sort by strength
        skills.sort(key=lambda s: s.strength, reverse=True)

        return [
            {
                "skill_id": s.skill_id,
                "name": s.name,
                "domain": s.domain,
                "strength": round(s.strength, 3),
                "level": s.get_level(),
                "usage_count": s.usage_count,
                "success_rate": (
                    round(s.success_count / max(s.usage_count, 1), 2)
                ),
                "last_used": s.last_used,
                "is_dormant": s.is_dormant,
                "is_meta": len(s.combined_from) > 0,
                "tags": s.tags,
            }
            for s in skills
        ]

    def get_learning_trajectory(self) -> dict:
        """
        Dapatkan gambaran progress pembelajaran dari waktu ke waktu.

        Returns:
            dict summary trajectory + breakdown per domain
        """
        all_skills = list(self._skills.values())

        if not all_skills:
            return {"message": "Belum ada skill yang tercatat", "skills": []}

        # Domain breakdown
        domain_summary: dict[str, dict] = {}
        for skill in all_skills:
            d = skill.domain
            if d not in domain_summary:
                domain_summary[d] = {
                    "skills": [],
                    "avg_strength": 0.0,
                    "total_usage": 0,
                }
            domain_summary[d]["skills"].append(skill.name)
            domain_summary[d]["total_usage"] += skill.usage_count

        for d in domain_summary:
            domain_skills = [s for s in all_skills if s.domain == d]
            domain_summary[d]["avg_strength"] = round(
                sum(s.strength for s in domain_skills) / len(domain_skills), 3
            )
            domain_summary[d]["skill_count"] = len(domain_summary[d]["skills"])

        # Overall stats
        total_skills = len(all_skills)
        avg_strength = round(sum(s.strength for s in all_skills) / total_skills, 3) if total_skills > 0 else 0
        meta_skills = [s for s in all_skills if s.combined_from]
        dormant = [s for s in all_skills if s.is_dormant]

        # Strongest and weakest
        sorted_skills = sorted(all_skills, key=lambda s: s.strength, reverse=True)
        strongest = sorted_skills[:3]
        weakest = [s for s in sorted_skills[-3:] if s.strength < 0.5]

        return {
            "total_skills": total_skills,
            "active_skills": total_skills - len(dormant),
            "dormant_skills": len(dormant),
            "meta_skills": len(meta_skills),
            "avg_strength": avg_strength,
            "overall_level": self._get_overall_level(avg_strength),
            "domains": list(domain_summary.keys()),
            "domain_summary": domain_summary,
            "strongest_skills": [
                {"name": s.name, "strength": round(s.strength, 3), "level": s.get_level()}
                for s in strongest
            ],
            "skills_needing_practice": [
                {"name": s.name, "strength": round(s.strength, 3), "advice": "Perlu self-play atau latihan lebih"}
                for s in weakest
            ],
            "trajectory_label": self._describe_trajectory(all_skills),
        }

    def consolidate(self) -> dict:
        """
        Merge skill-skill yang tumpang tindih atau sangat mirip.

        Returns:
            dict info konsolidasi
        """
        all_skills = list(self._skills.values())
        merged = []
        to_remove = set()

        for i, skill_a in enumerate(all_skills):
            if skill_a.skill_id in to_remove:
                continue
            for skill_b in all_skills[i + 1:]:
                if skill_b.skill_id in to_remove:
                    continue
                # Cek similarity nama
                similarity = self._name_similarity(skill_a.name, skill_b.name)
                if similarity > 0.7 and skill_a.domain == skill_b.domain:
                    # Merge: ambil yang lebih kuat, gabungkan usage count
                    stronger = skill_a if skill_a.strength >= skill_b.strength else skill_b
                    weaker = skill_b if stronger == skill_a else skill_a

                    stronger.usage_count += weaker.usage_count
                    stronger.success_count += weaker.success_count
                    stronger.strength = min(MAX_STRENGTH, stronger.strength + weaker.strength * 0.1)

                    to_remove.add(weaker.skill_id)
                    merged.append({
                        "merged": weaker.name,
                        "into": stronger.name,
                        "similarity": round(similarity, 2),
                    })

        # Remove merged skills
        for sid in to_remove:
            del self._skills[sid]

        self._save_skills()

        return {
            "merged_count": len(merged),
            "merges": merged,
            "skills_remaining": len(self._skills),
        }

    # ─── PRIVATE METHODS ───

    def _get_challenge_templates(self, level: str, domain: str) -> list[dict]:
        """Dapatkan template challenge berdasarkan level skill."""
        base_challenges = [
            {
                "type": "explain_simple",
                "description": "Jelaskan konsep '{skill}' dalam 3 kalimat untuk orang awam",
                "difficulty": 0.3,
            },
            {
                "type": "apply_example",
                "description": "Berikan contoh nyata penggunaan '{skill}' dalam kehidupan sehari-hari",
                "difficulty": 0.4,
            },
            {
                "type": "compare_contrast",
                "description": "Bandingkan '{skill}' dengan pendekatan alternatif — kapan pakai yang mana?",
                "difficulty": 0.5,
            },
            {
                "type": "edge_case",
                "description": "Identifikasi 2 edge case di mana '{skill}' tidak efektif atau gagal",
                "difficulty": 0.6,
            },
            {
                "type": "teach_back",
                "description": "Ajarkan '{skill}' dari awal — buat kurikulum 3-step untuk pemula",
                "difficulty": 0.7,
            },
            {
                "type": "cross_domain",
                "description": f"Bagaimana '{'{skill}'}' bisa diaplikasikan ke domain {domain} dengan cara yang tidak konvensional?",
                "difficulty": 0.8,
            },
        ]

        # Sesuaikan difficulty range berdasarkan level
        if level == "beginner":
            return [c for c in base_challenges if c["difficulty"] <= 0.4]
        elif level == "developing":
            return [c for c in base_challenges if c["difficulty"] <= 0.6]
        elif level == "proficient":
            return [c for c in base_challenges if c["difficulty"] <= 0.8]
        else:
            return base_challenges

    def _simulate_attempt(self, skill_strength: float, difficulty: float) -> float:
        """
        Simulasi kualitas attempt berdasarkan strength vs difficulty.

        Dalam real SIDIX: ini diganti dengan actual LLM attempt + evaluator.
        """
        # Base quality = strength - difficulty_penalty
        base = skill_strength - (difficulty * 0.3)

        # Add noise (meniru variasi performa nyata)
        import random
        noise = (random.random() - 0.5) * 0.2

        quality = max(0.0, min(1.0, base + noise + 0.2))
        return quality

    def _generate_feedback(self, quality: float, challenge: dict) -> str:
        """Generate feedback untuk attempt."""
        if quality >= 0.8:
            return f"Excellent! Kamu handle challenge '{challenge['type']}' dengan sangat baik."
        elif quality >= 0.6:
            return f"Good. Challenge '{challenge['type']}' berhasil diselesaikan, ada ruang untuk improvement."
        elif quality >= 0.4:
            return f"Partial. Challenge '{challenge['type']}' perlu latihan lebih — ada gap yang terlihat."
        else:
            return f"Perlu latihan. Challenge '{challenge['type']}' mengungkap area yang perlu diperkuat."

    def _get_overall_level(self, avg_strength: float) -> str:
        """Label level keseluruhan."""
        if avg_strength >= 0.85:
            return "Grandmaster"
        elif avg_strength >= 0.7:
            return "Expert"
        elif avg_strength >= 0.5:
            return "Practitioner"
        elif avg_strength >= 0.3:
            return "Student"
        else:
            return "Beginner"

    def _describe_trajectory(self, skills: list) -> str:
        """Describe learning trajectory dalam satu kalimat."""
        total = len(skills)
        strong = sum(1 for s in skills if s.strength >= 0.7)
        developing = sum(1 for s in skills if 0.3 <= s.strength < 0.7)

        if total == 0:
            return "Belum ada skill"
        elif strong >= total * 0.7:
            return "Solid expertise — mayoritas skill sudah kuat"
        elif developing >= total * 0.5:
            return "Dalam proses — banyak skill sedang berkembang"
        else:
            return "Early stage — masih banyak ruang untuk tumbuh"

    def _name_similarity(self, name_a: str, name_b: str) -> float:
        """Simple similarity berbasis overlap kata."""
        words_a = set(name_a.lower().split())
        words_b = set(name_b.lower().split())
        if not words_a or not words_b:
            return 0.0
        intersection = len(words_a & words_b)
        union = len(words_a | words_b)
        return intersection / union

    def _save_skills(self) -> None:
        """Simpan semua skills ke file JSON."""
        try:
            skills_file = self.data_dir / "skills.json"
            data = {sid: skill.to_dict() for sid, skill in self._skills.items()}
            with open(skills_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            pass  # Fail silently untuk dependencies yang tidak tersedia

    def _load_skills(self) -> None:
        """Load skills dari file JSON."""
        try:
            skills_file = self.data_dir / "skills.json"
            if skills_file.exists():
                with open(skills_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for sid, skill_dict in data.items():
                    self._skills[sid] = Skill.from_dict(skill_dict)
        except Exception:
            pass


# ─────────────────────────────────────────────
# SINGLETON & SHORTCUTS
# ─────────────────────────────────────────────

_default_learner: Optional[PermanentLearning] = None


def get_learner(data_dir: Optional[str] = None) -> PermanentLearning:
    """Dapatkan instance PermanentLearning default."""
    global _default_learner
    if _default_learner is None:
        _default_learner = PermanentLearning(
            data_dir=Path(data_dir) if data_dir else None
        )
    return _default_learner


def learn(skill_name: str, domain: str, description: str = "") -> dict:
    """Shortcut: tambahkan skill baru."""
    return get_learner().add_skill(skill_name, domain, description)


def practice(skill_name: str, success: bool = True, context: str = "") -> dict:
    """Shortcut: reinforce skill dengan satu penggunaan."""
    return get_learner().reinforce_skill(skill_name, {"success": success, "description": context})


def spin(skill_name: str, rounds: int = 3) -> list[dict]:
    """Shortcut: jalankan self-play SPIN."""
    return get_learner().self_play(skill_name, rounds)
