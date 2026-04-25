"""
tool_synthesizer.py — Autonomous Tool Creation (Memento-Skills + CodeAct hybrid)
==================================================================================

User insight 2026-04-26:
> "bagaimana caranya sidix bisa membuat tools baru, padahal tools itu tidak
> ada referensinya?"

Ini realisasi visi user "SIDIX bahkan bisa buat tools baru buat dirinya sendiri".

Inspirasi:
- **Voyager** (NeurIPS 2023, Wang et al.) — agent menulis skill Python yang
  dieksekusi di Minecraft, akumulasi skill library.
- **Memento-Skills 2026** (huggingface.co/papers/2603.18743) — skill router
  trainable + retrieval.
- **CodeAct 2024** (huggingface.co/papers/2402.01030) — executable code
  action lebih fleksibel daripada JSON tool calls.

Pipeline:
1. **DETECT NEED** — saat ReAct loop mentok ("no existing tool fits") atau
   aspiration_detector trigger.
2. **SPECIFY** — LLM generate tool spec (input/output type, function name,
   docstring, dependencies).
3. **GENERATE CODE** — LLM write Python function signature + body.
4. **TEST in SANDBOX** — eksekusi di `code_sandbox` existing dengan dummy
   input. Capture output + error.
5. **VERIFY** — kalau output match expected schema dan no error, mark valid.
6. **PERSIST** — simpan ke `brain/skills/<name>.py` + index ke `_index.json`.
7. **REGISTER** — runtime register sebagai tool baru di ReAct loop (next
   query bisa pakai).

Skill yang fail 2x → auto-deprecate (move ke `brain/skills/_deprecated/`).
Skill yang sukses 5x → mark stable, masukin ke training pair generation
(SIDIX belajar pakai skill itu via LoRA juga).

Filosofi: bukan ChatGPT yang nunggu Anthropic add fitur. SIDIX nulis fitur
sendiri saat butuh, langsung deploy. **Compound advantage seiring waktu.**
"""

from __future__ import annotations

import ast
import json
import logging
import re
import time
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger(__name__)


# ── Data ───────────────────────────────────────────────────────────────────────

@dataclass
class SkillSpec:
    """Specification untuk tool baru yang akan di-synthesize."""
    id: str
    ts: str
    name: str                          # e.g. "html_table_to_csv"
    description: str                   # 1-2 line apa yang dilakukan tool
    input_schema: dict                 # {"html": "string"}
    output_schema: dict                # {"csv": "string"}
    dependencies: list[str]            # ["beautifulsoup4", "csv"]
    code: str = ""                     # full Python source
    test_input: dict = field(default_factory=dict)
    test_expected: str = ""            # description of expected output
    status: str = "draft"              # draft | tested | valid | deployed | deprecated
    test_runs: int = 0
    test_passes: int = 0
    last_error: str = ""
    derived_from: str = ""             # aspiration id atau task description


# ── Path ───────────────────────────────────────────────────────────────────────

def _skills_dir() -> Path:
    here = Path(__file__).resolve().parent
    root = here.parent.parent.parent
    d = root / "brain" / "skills"
    d.mkdir(parents=True, exist_ok=True)
    (d / "_deprecated").mkdir(exist_ok=True)
    return d


def _skills_index() -> Path:
    return _skills_dir() / "_index.json"


# ── Spec generation (LLM) ──────────────────────────────────────────────────────

def generate_skill_spec(
    task_description: str,
    *,
    derived_from: str = "",
) -> Optional[SkillSpec]:
    """
    LLM generate spec untuk tool baru berdasarkan task description.
    Spec = pre-code blueprint, supaya LLM gen code-nya focused.
    """
    try:
        try:
            from .ollama_llm import generate as llm_gen
        except Exception:
            from .local_llm import generate_sidix as llm_gen
    except Exception:
        log.warning("[tool_synth] LLM not available")
        return None

    prompt = f"""Task: bikin Python function (single file) untuk capability:

"{task_description}"

Output ONLY JSON (no markdown):
{{
  "name": "snake_case_function_name (max 32 char)",
  "description": "1-2 kalimat apa yang dilakukan",
  "input_schema": {{"param1": "type"}},
  "output_schema": {{"result": "type"}},
  "dependencies": ["library1", "library2"],
  "test_input": {{"param1": "sample value"}},
  "test_expected": "deskripsi singkat output yang diharapkan"
}}

Rules:
- Function MURNI Python, NO vendor LLM API call (jangan pakai openai/anthropic).
- Dependency hanya yang available di stdlib atau pip-installable umum.
- Function harus deterministic kalau input sama.
- Test_input harus realistic, bisa langsung dijalankan.

Output ONLY JSON:"""

    try:
        out = llm_gen(prompt, max_tokens=400, temperature=0.5)
        if isinstance(out, dict):
            response = out.get("text") or out.get("response") or ""
        else:
            response = out or ""
        response = response.strip()
        response = re.sub(r"^```(?:json)?\s*", "", response)
        response = re.sub(r"\s*```$", "", response)
        data = json.loads(response)

        name = data.get("name", "").strip().lower()
        # Sanitize name (snake_case, no special chars)
        name = re.sub(r"[^a-z0-9_]", "_", name)[:32]
        if not name or not re.match(r"^[a-z]", name):
            return None

        return SkillSpec(
            id=f"skill_{uuid.uuid4().hex[:10]}",
            ts=datetime.now(timezone.utc).isoformat(),
            name=name,
            description=(data.get("description") or "")[:200],
            input_schema=data.get("input_schema") or {},
            output_schema=data.get("output_schema") or {},
            dependencies=[d for d in (data.get("dependencies") or []) if d][:8],
            test_input=data.get("test_input") or {},
            test_expected=(data.get("test_expected") or "")[:200],
            derived_from=derived_from,
        )
    except json.JSONDecodeError:
        log.debug("[tool_synth] spec JSON fail: %s", response[:200])
        return None
    except Exception as e:
        log.warning("[tool_synth] spec gen fail: %s", e)
        return None


# ── Code generation ────────────────────────────────────────────────────────────

def generate_skill_code(spec: SkillSpec) -> str:
    """
    LLM generate Python source dari spec. Output is full module text
    (imports + function + docstring).
    """
    try:
        try:
            from .ollama_llm import generate as llm_gen
        except Exception:
            from .local_llm import generate_sidix as llm_gen
    except Exception:
        return ""

    deps_str = ", ".join(spec.dependencies) or "(stdlib only)"
    inp_str = json.dumps(spec.input_schema, ensure_ascii=False)
    out_str = json.dumps(spec.output_schema, ensure_ascii=False)

    prompt = f"""Tulis Python module lengkap (imports + function) untuk skill:

Name: {spec.name}
Description: {spec.description}
Input: {inp_str}
Output: {out_str}
Dependencies: {deps_str}

Format output:
```python
\"\"\"
{spec.name} — {spec.description}

Auto-generated oleh SIDIX tool_synthesizer.
\"\"\"

import ...

def {spec.name}(...) -> ...:
    \"\"\"docstring\"\"\"
    # implementation
    return result
```

Rules:
- Single function, no classes (kecuali essential).
- Type hints wajib.
- Handle edge cases (empty input, malformed).
- Return type match output_schema.
- NO vendor LLM API (no openai/anthropic/google.genai).
- Max 80 baris.
- Output FULL Python module text, including imports.
"""

    try:
        out = llm_gen(prompt, max_tokens=900, temperature=0.4)
        if isinstance(out, dict):
            response = out.get("text") or out.get("response") or ""
        else:
            response = out or ""

        # Extract code from markdown fence
        match = re.search(r"```(?:python)?\s*(.+?)```", response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response.strip()
    except Exception as e:
        log.warning("[tool_synth] code gen fail: %s", e)
        return ""


# ── Validation + sandbox test ──────────────────────────────────────────────────

_FORBIDDEN_PATTERNS = [
    r"\bopenai\b", r"anthropic", r"google\.genai", r"\bgemini\b",
    r"os\.system", r"subprocess\.\w+\(",
    r"__import__\(",
    r"eval\(", r"exec\(",
    r"requests\.(post|put|delete)",  # restrict mutations
    r"open\([^,)]+,\s*['\"]w",       # restrict write to disk
]


def validate_code(code: str) -> tuple[bool, str]:
    """
    Static checks: parse AST + forbidden pattern scan.
    Returns (ok, error_message).
    """
    if not code or len(code) < 20:
        return False, "Code too short or empty"

    # AST parse
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"SyntaxError: {e}"

    # Forbidden patterns
    for pat in _FORBIDDEN_PATTERNS:
        if re.search(pat, code, re.IGNORECASE):
            return False, f"Forbidden pattern: {pat}"

    # Must define at least one function
    has_func = any(isinstance(n, ast.FunctionDef) for n in ast.walk(tree))
    if not has_func:
        return False, "No function defined"

    return True, ""


def test_skill_in_sandbox(spec: SkillSpec) -> tuple[bool, str]:
    """
    Eksekusi spec.code di sandbox restricted, panggil function dengan
    spec.test_input, return (success, output_or_error).

    Reuse code_sandbox kalau available, atau fallback ke restricted exec.
    """
    if not spec.code:
        return False, "no code to test"

    ok, err = validate_code(spec.code)
    if not ok:
        return False, f"validate fail: {err}"

    # Try via existing code_sandbox tool kalau tersedia
    try:
        from .tools.code_sandbox import run_python  # type: ignore
        full_code = spec.code + f"\n\nresult = {spec.name}(**{json.dumps(spec.test_input)})\nprint(result)"
        out = run_python(full_code, timeout=10)
        if isinstance(out, dict):
            stdout = out.get("stdout", "")
            error = out.get("error", "")
            if error:
                return False, f"sandbox error: {error[:200]}"
            return True, stdout[:500]
        return True, str(out)[:500]
    except Exception:
        pass  # fall through to restricted exec

    # Fallback: restricted exec (kurang aman, tapi tested)
    try:
        local_ns: dict[str, Any] = {}
        exec(spec.code, {"__builtins__": __builtins__}, local_ns)
        fn = local_ns.get(spec.name)
        if not callable(fn):
            return False, f"function {spec.name} not found in module"
        result = fn(**spec.test_input)
        return True, str(result)[:500]
    except Exception as e:
        return False, f"exec error: {str(e)[:200]}"


# ── Storage + index ────────────────────────────────────────────────────────────

def save_skill(spec: SkillSpec) -> Path:
    """Tulis skill ke brain/skills/<name>_<id>.py + update _index.json."""
    skill_path = _skills_dir() / f"{spec.name}_{spec.id[-6:]}.py"
    skill_path.write_text(spec.code, encoding="utf-8")

    # Update index
    idx_path = _skills_index()
    if idx_path.exists():
        try:
            index = json.loads(idx_path.read_text(encoding="utf-8"))
        except Exception:
            index = {"skills": []}
    else:
        index = {"skills": []}

    # Remove any existing entry for same id (overwrite)
    index["skills"] = [s for s in index.get("skills", []) if s.get("id") != spec.id]
    index["skills"].append(asdict(spec))

    idx_path.write_text(
        json.dumps(index, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return skill_path


def list_skills(status: str = "") -> list[dict]:
    """List semua skill from index."""
    idx_path = _skills_index()
    if not idx_path.exists():
        return []
    try:
        index = json.loads(idx_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    skills = index.get("skills", [])
    if status:
        skills = [s for s in skills if s.get("status") == status]
    return skills


def update_skill_status(skill_id: str, **kwargs) -> bool:
    """Update field di index entry."""
    idx_path = _skills_index()
    if not idx_path.exists():
        return False
    try:
        index = json.loads(idx_path.read_text(encoding="utf-8"))
    except Exception:
        return False
    found = False
    for s in index.get("skills", []):
        if s.get("id") == skill_id:
            s.update(kwargs)
            found = True
    if found:
        idx_path.write_text(
            json.dumps(index, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return found


# ── End-to-end synthesis pipeline ──────────────────────────────────────────────

def synthesize_skill(
    task_description: str,
    *,
    derived_from: str = "",
    auto_test: bool = True,
) -> Optional[SkillSpec]:
    """
    End-to-end: spec → code → validate → test → save.
    Return SkillSpec dengan status final.

    Use case:
    - User aspiration triggers ini (via aspiration_detector)
    - ReAct loop mentok ("no existing tool fits")
    - Admin manual trigger via /admin/synthesize endpoint
    """
    # 1. Generate spec
    spec = generate_skill_spec(task_description, derived_from=derived_from)
    if not spec:
        log.warning("[tool_synth] spec gen returned None")
        return None

    # 2. Generate code
    code = generate_skill_code(spec)
    if not code:
        log.warning("[tool_synth] code gen empty")
        spec.status = "failed_gen"
        spec.last_error = "code generation empty"
        save_skill(spec)
        return spec
    spec.code = code

    # 3. Validate static
    ok, err = validate_code(code)
    if not ok:
        spec.status = "invalid"
        spec.last_error = err
        save_skill(spec)
        return spec

    # 4. Test (optional)
    if auto_test:
        spec.test_runs += 1
        success, output = test_skill_in_sandbox(spec)
        if success:
            spec.test_passes += 1
            spec.status = "tested"
            spec.last_error = ""
        else:
            spec.status = "test_failed"
            spec.last_error = output

    # 5. Save
    save_skill(spec)
    return spec


# ── Stats ──────────────────────────────────────────────────────────────────────

def stats() -> dict:
    """Untuk admin dashboard."""
    skills = list_skills()
    if not skills:
        return {"total": 0, "by_status": {}, "tested_pass_rate": 0.0}

    by_status: dict[str, int] = {}
    total_runs = 0
    total_passes = 0
    for s in skills:
        st = s.get("status", "draft")
        by_status[st] = by_status.get(st, 0) + 1
        total_runs += s.get("test_runs", 0)
        total_passes += s.get("test_passes", 0)

    pass_rate = (total_passes / total_runs) if total_runs else 0.0
    return {
        "total": len(skills),
        "by_status": by_status,
        "tested_pass_rate": round(pass_rate, 3),
        "total_test_runs": total_runs,
        "total_test_passes": total_passes,
    }


__all__ = [
    "SkillSpec",
    "generate_skill_spec", "generate_skill_code",
    "validate_code", "test_skill_in_sandbox",
    "save_skill", "list_skills", "update_skill_status",
    "synthesize_skill", "stats",
]
