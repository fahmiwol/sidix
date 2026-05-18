"""
coding_planner.py — LLM-based planner khusus untuk coding tasks.

SIDIX ReAct loop menggunakan rule-based planner (`_rule_based_plan`) untuk
kebanyakan intent. Tapi untuk coding — yang memerlukan chaining multi-step
seperti: baca file → analisis → edit → test → fix — rule-based tidak cukup.

Modul ini menyediakan `plan_coding_step()` yang:
  1. Menerima pertanyaan user + history ReAct step + nomor step
  2. Prompt Ollama untuk memutuskan tool + args optimal
  3. Parse output ke format (thought, action_name, action_args)
  4. Validasi action_name terhadap TOOL_REGISTRY
  5. Fallback ke heuristic jika LLM output malformed

Prinsip:
  - Self-hosted: hanya pakai Ollama lokal, tidak ada vendor API.
  - Deterministic fallback: kalau LLM gagal, jangan hang — fallback ke heuristic.
  - Fast: max_tokens kecil (~256), temperature rendah (0.3) untuk planner.

Digunakan oleh: agent_react.py (diinject saat coding intent terdeteksi).
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from .ollama_llm import ollama_generate

log = logging.getLogger("sidix.coding_planner")

# ── Coding Tool Subset ───────────────────────────────────────────────────────
# Tools yang relevan untuk coding tasks. Planner HANYA boleh memilih dari sini.
_CODING_TOOLS = {
    "workspace_list": (
        "List isi folder sandbox. Params: path (opsional), max_entries (opsional). "
        "Gunakan saat: ingin tahu file apa saja yang ada di project."
    ),
    "workspace_read": (
        "Baca isi satu file teks. Params: path (wajib). "
        "Gunakan saat: perlu melihat kode sebelum mengedit atau menganalisis."
    ),
    "workspace_write": (
        "Tulis/overwrite file teks baru. RESTRICTED. Params: path (wajib), content (wajib). "
        "Gunakan saat: membuat file baru atau menulis ulang file dari nol."
    ),
    "workspace_patch": (
        "Apply unified diff/patch ke file existing. Params: path (wajib), patch (wajib). "
        "Gunakan saat: mengedit sebagian kecil file yang sudah ada (refactor, fix bug, tambah fungsi)."
    ),
    "code_sandbox": (
        "Jalankan snippet Python di subprocess terisolasi. Params: code (wajib). "
        "Gunakan saat: hitung, transformasi data, simulasi, atau parse teks."
    ),
    "code_analyze": (
        "Analisis struktur kode (AST): fungsi, class, imports, complexity. Params: code (wajib), filename (opsional). "
        "Gunakan saat: ingin memahami struktur kode tanpa mengeksekusinya."
    ),
    "code_validate": (
        "Validasi syntax kode Python/JS/TS/SQL/HTML. Params: code (wajib), language (opsional). "
        "Gunakan saat: memastikan kode yang ditulis tidak ada syntax error."
    ),
    "project_map": (
        "Generate tree view struktur folder project. Params: path (opsional), max_depth (opsional). "
        "Gunakan saat: butuh gambaran besar project (file apa saja, di mana)."
    ),
    "shell_run": (
        "Jalankan shell command (npm, pip, git, pytest, dll). RESTRICTED. Params: command (wajib), cwd (opsional). "
        "Gunakan saat: install dependency, run test, git status, build project."
    ),
    "test_run": (
        "Jalankan test suite (pytest, jest, cargo test, dll). Params: path (opsional), framework (opsional). "
        "Gunakan saat: memverifikasi kode setelah edit/fix."
    ),
    "git_status": (
        "Lihat status git (modified, staged, untracked). Params: path (opsional). "
        "Gunakan saat: ingin tahu perubahan apa saja di repo."
    ),
    "git_diff": (
        "Lihat diff perubahan git. Params: path (opsional), staged (opsional). "
        "Gunakan saat: ingin review perubahan sebelum commit."
    ),
    "web_fetch": (
        "Fetch halaman web (dokumentasi, tutorial, GitHub). Params: url (wajib). "
        "Gunakan saat: butuh referensi dokumentasi library/framework."
    ),
    "web_search": (
        "Cari web via DuckDuckGo. Params: query (wajib). "
        "Gunakan saat: butuh informasi umum yang tidak ada di corpus."
    ),
}

# ── Prompt Template ──────────────────────────────────────────────────────────

_CODING_PLANNER_SYSTEM = """Kamu adalah Coding Planner untuk SIDIX — AI coding assistant self-hosted.
Tugasmu: berdasarkan pertanyaan user dan history langkah sebelumnya, putuskan TOOL BERIKUTNYA yang paling tepat.

Aturan:
1. HANYA pilih tool dari daftar yang diberikan. Jangan gunakan tool di luar daftar.
2. Kalau sudah cukup informasi untuk menjawab, pilih action "final_answer".
3. Kalau butuh informasi lebih, pilih SATU tool yang paling relevan.
4. Args harus valid JSON object (bisa kosong {} kalau tidak butuh parameter).
5. Jangan berulang tool yang sama dengan args identik — kalau sudah pernah, pilih tool lain atau final_answer.
6. Untuk edit file existing, prioritaskan workspace_patch (surgical edit) dibanding workspace_write (overwrite total).
7. Untuk file baru, gunakan workspace_write.

Format output (WAJIB):
THOUGHT: <pikiran singkat mengapa tool ini dipilih>
ACTION: <nama_tool>
ARGS: <json object parameter>

Contoh:
THOUGHT: User minta fix bug di fungsi calculate. Saya perlu baca file dulu untuk lihat kodenya.
ACTION: workspace_read
ARGS: {"path": "utils.py"}

Contoh 2:
THOUGHT: Setelah baca file, saya tahu bugnya di line 15. Saya akan apply patch untuk fix.
ACTION: workspace_patch
ARGS: {"path": "utils.py", "patch": "--- a/utils.py\\n+++ b/utils.py\\n@@ -12,7 +12,7 @@ def calculate(x):\\n-    return x / 0\\n+    return x / 1\\n"}

Contoh 3:
THOUGHT: Saya sudah baca file, apply patch, dan run test — semua passed. Jawaban sudah lengkap.
ACTION: final_answer
ARGS: {}
"""

# ── Intent Detection ─────────────────────────────────────────────────────────

_CODING_KEYWORDS = (
    "code", "coding", "program", "programming", "bug", "fix", "debug",
    "error", "exception", "traceback", "refactor", "function", "class",
    "module", "import", "npm", "pip", "install", "package", "dependency",
    "test", "pytest", "unittest", "jest", "build", "compile", "run",
    "git", "commit", "branch", "merge", "pull", "push", "repo",
    "api", "endpoint", "route", "crud", "fastapi", "flask", "django",
    "react", "vue", "angular", "next.js", "javascript", "typescript",
    "python", "html", "css", "sql", "database", "query",
    "docker", "dockerfile", "compose", "container",
    "scaffold", "template", "boilerplate", "generate app",
    "file", "folder", "workspace", "project", "src",
)

_CODING_REGEX = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in _CODING_KEYWORDS) + r")\b",
    re.IGNORECASE,
)


def is_coding_intent(question: str) -> bool:
    """Deteksi apakah pertanyaan user adalah coding intent."""
    if not question:
        return False
    return bool(_CODING_REGEX.search(question))


# ── Planner Core ─────────────────────────────────────────────────────────────


def plan_coding_step(
    question: str,
    history: list[Any],
    step: int,
    available_tools: dict[str, Any] | None = None,
    workspace_files: list[str] | None = None,
) -> tuple[str, str, dict]:
    """
    Plan satu step ReAct untuk coding task.

    Args:
        question: Pertanyaan/intent user.
        history: List of ReActStep (atau dict dengan keys: action_name, action_args, observation).
        step: Nomor step saat ini (0-based).
        available_tools: TOOL_REGISTRY subset yang boleh dipakai (default: _CODING_TOOLS).
        workspace_files: List file yang sudah diketahui ada di workspace (opsional, untuk konteks).

    Returns:
        (thought, action_name, action_args)
        action_name == "" berarti final_answer.
    """
    tools = available_tools or _CODING_TOOLS

    # Build history context (ringkas)
    history_text = _format_history(history, max_steps=4)

    # Build workspace context
    workspace_hint = ""
    if workspace_files:
        file_list = ", ".join(workspace_files[:20])
        workspace_hint = f"\nFile yang tersedia di workspace: {file_list}\n"

    # Build tool descriptions
    tool_desc = "\n".join(
        f"- {name}: {desc}" for name, desc in tools.items()
    )

    prompt = f"""Pertanyaan user: {question}

Step saat ini: {step + 1}
{workspace_hint}
History langkah sebelumnya:
{history_text}

Tool yang tersedia:
{tool_desc}

ACTION: """

    try:
        text, mode = ollama_generate(
            prompt=prompt,
            system=_CODING_PLANNER_SYSTEM,
            max_tokens=256,
            temperature=0.3,
        )
        if mode == "mock_error" or not text:
            log.warning("Coding planner LLM failed, falling back to heuristic")
            return _heuristic_fallback(question, history, step)

        return _parse_planner_output(text, tools)

    except Exception as e:
        log.warning(f"Coding planner exception: {e}")
        return _heuristic_fallback(question, history, step)


def _format_history(history: list[Any], max_steps: int = 4) -> str:
    """Format history ReAct jadi text ringkas untuk prompt."""
    if not history:
        return "(belum ada langkah sebelumnya)"

    lines = []
    # Ambil max_steps terakhir
    recent = history[-max_steps:] if len(history) > max_steps else history
    for i, h in enumerate(recent, 1):
        action = getattr(h, "action_name", "") or h.get("action_name", "")
        args = getattr(h, "action_args", {}) or h.get("action_args", {})
        obs = getattr(h, "observation", "") or h.get("observation", "")
        # Truncate observation
        obs_short = (obs[:200] + "...") if len(obs) > 200 else obs
        lines.append(f"  Step {i}: {action}({json.dumps(args, ensure_ascii=False)}) → {obs_short}")
    return "\n".join(lines) or "(belum ada langkah sebelumnya)"


# ── Output Parser ────────────────────────────────────────────────────────────

_THOUGHT_RE = re.compile(r"THOUGHT:\s*(.+?)(?=\nACTION:|$)", re.IGNORECASE | re.DOTALL)
_ACTION_RE = re.compile(r"ACTION:\s*(\S+)")
_ARGS_RE = re.compile(r"ARGS:\s*(\{.*?\})", re.DOTALL)


def _parse_planner_output(
    text: str, tools: dict[str, str]
) -> tuple[str, str, dict]:
    """
    Parse output LLM ke (thought, action_name, action_args).
    """
    thought = ""
    action = ""
    args: dict = {}

    # Extract THOUGHT
    m = _THOUGHT_RE.search(text)
    if m:
        thought = m.group(1).strip().replace("\n", " ")

    # Extract ACTION
    m = _ACTION_RE.search(text)
    if m:
        action = m.group(1).strip().lower()

    # Extract ARGS
    m = _ARGS_RE.search(text)
    if m:
        try:
            args = json.loads(m.group(1))
        except json.JSONDecodeError:
            # Fallback: coba parse dengan regex sederhana
            args = _loose_json_parse(m.group(1))

    # Validate action
    if action == "final_answer":
        return (thought or "Saya sudah punya cukup informasi untuk menjawab.", "", args)

    if action not in tools:
        # Empty action = LLM didn't follow ACTION: format. Common, downgrade to debug
        # to avoid log spam. Only warn for non-empty unrecognized action names.
        if action:
            log.warning(f"Coding planner chose invalid action: {action!r}")
        else:
            log.debug("Coding planner output missing ACTION: line, using heuristic fallback")
        return _heuristic_fallback("", [], 0)

    return thought or f"Plan: gunakan {action}", action, args


def _loose_json_parse(raw: str) -> dict:
    """Parse JSON yang mungkin malformed (common LLM issues)."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Coba fix: replace single quotes, trailing commas
        fixed = raw.replace("'", '"')
        fixed = re.sub(r",\s*}", "}", fixed)
        fixed = re.sub(r",\s*]", "]", fixed)
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            return {}


# ── Heuristic Fallback ───────────────────────────────────────────────────────


def _heuristic_fallback(
    question: str,
    history: list[Any],
    step: int,
) -> tuple[str, str, dict]:
    """
    Fallback heuristic ketika LLM planner gagal.
    Menggunakan pola sederhana berbasis step number.
    """
    q_lower = (question or "").lower()

    # Step 0: selalu mulai dengan project_map atau workspace_list untuk orientasi
    if step == 0:
        if any(k in q_lower for k in ("bug", "error", "fix", "refactor")):
            return (
                "User melaporkan bug/error. Saya perlu melihat struktur project dulu.",
                "project_map",
                {},
            )
        if any(k in q_lower for k in ("buat", "bikin", "generate", "scaffold", "create", "new")):
            return (
                "User minta membuat project/file baru. Saya perlu cek workspace dulu.",
                "workspace_list",
                {},
            )
        return (
            "User minta bantuan coding. Saya mulai dengan melihat struktur project.",
            "project_map",
            {},
        )

    # Step 1: kalau step 0 adalah project_map/workspace_list, baca file yang relevan
    if step == 1 and history:
        last_action = getattr(history[-1], "action_name", "") or history[-1].get("action_name", "")
        if last_action in ("project_map", "workspace_list"):
            return (
                "Struktur project sudah diketahui. Saya perlu baca file utama untuk analisis.",
                "workspace_read",
                {"path": ""},  # Agen perlu isi path berdasarkan konteks
            )

    # Step terakhir: final answer
    if step >= 3:
        return (
            "Saya sudah mengumpulkan informasi yang cukup. Langsung jawab user.",
            "",
            {},
        )

    # Default: coba baca file
    return (
        "Saya perlu membaca file relevan untuk memahami konteks.",
        "workspace_read",
        {"path": ""},
    )
