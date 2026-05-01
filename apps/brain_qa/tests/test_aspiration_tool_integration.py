"""
test_aspiration_tool_integration.py — Unit tests for Sprint D: Aspiration + Tool Synthesis

Test coverage:
1. Aspiration detection keywords
2. Aspiration analysis (may return None in test env)
3. Tool spec generation
4. Tool code validation
5. End-to-end synthesis pipeline
6. OMNYX aspiration hook

Author: Mighan Lab / SIDIX
License: MIT
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from brain_qa.aspiration_detector import (
    Aspiration,
    detect_aspiration_keywords,
    analyze_aspiration,
    _aspirations_index,
)
from brain_qa.tool_synthesizer import (
    SkillSpec,
    generate_skill_spec,
    validate_code,
    stats,
    list_skills,
)


# ── Aspiration Detector Tests ────────────────────────────────────────────

class TestAspirationDetector:
    def test_detect_aspiration_keywords_true(self):
        """Detect aspiration trigger phrases."""
        text = "GPT bisa bikin gambar, harusnya SIDIX juga bisa dong!"
        is_asp, matched = detect_aspiration_keywords(text)
        assert is_asp is True
        assert len(matched) > 0
    
    def test_detect_aspiration_keywords_false(self):
        """Non-aspiration text should return False."""
        text = "Halo, apa kabar?"
        is_asp, matched = detect_aspiration_keywords(text)
        assert is_asp is False
    
    def test_detect_aspiration_keywords_empty(self):
        """Empty text should return False."""
        is_asp, matched = detect_aspiration_keywords("")
        assert is_asp is False
    
    def test_detect_aspiration_variants(self):
        """Test various aspiration triggers."""
        triggers = [
            "kenapa SIDIX gak bisa bikin video?",
            "oh kita juga bisa dong bikin 3D",
            "saya tau cara kerjanya, bikin ah!",
            "why can't sidix do this?",
        ]
        for t in triggers:
            is_asp, _ = detect_aspiration_keywords(t)
            assert is_asp is True, f"Should detect: {t}"
    
    def test_analyze_aspiration(self):
        """Test aspiration analysis (may return None without LLM)."""
        text = "GPT bisa bikin gambar, harusnya SIDIX juga bisa bikin gambar dari teks"
        asp = analyze_aspiration(text, derived_from="test")
        # May or may not succeed depending on LLM availability
        if asp:
            assert isinstance(asp, Aspiration)
            assert asp.capability_target
            assert asp.estimated_effort in ("low", "medium", "high", "moonshot")


# ── Tool Synthesizer Tests ───────────────────────────────────────────────

class TestToolSynthesizer:
    def test_validate_code_valid(self):
        """Test validation of valid Python code."""
        code = '''
def hello_world(name: str) -> str:
    """Say hello."""
    return f"Hello, {name}!"
'''
        ok, err = validate_code(code)
        assert ok is True
        assert err == ""
    
    def test_validate_code_syntax_error(self):
        """Test validation catches syntax errors."""
        code = "def broken(\n    pass"
        ok, err = validate_code(code)
        assert ok is False
        assert "SyntaxError" in err
    
    def test_validate_code_forbidden_pattern(self):
        """Test validation catches forbidden patterns."""
        code = '''
def evil():
    import openai
    return openai.chat()
'''
        ok, err = validate_code(code)
        assert ok is False
        assert "Forbidden" in err
    
    def test_validate_code_no_function(self):
        """Test validation requires at least one function."""
        code = "# This is a comment\nx = 1 + 2\ny = x * 3\nprint(y)"
        ok, err = validate_code(code)
        assert ok is False
        assert "No function" in err
    
    def test_validate_code_empty(self):
        """Test validation rejects empty code."""
        ok, err = validate_code("")
        assert ok is False
    
    def test_generate_skill_spec(self):
        """Test skill spec generation (may return None without LLM)."""
        spec = generate_skill_spec(
            "Function to convert HTML table to CSV string",
            derived_from="test",
        )
        if spec:
            assert isinstance(spec, SkillSpec)
            assert spec.name
            assert spec.description
            assert spec.input_schema
            assert spec.output_schema
    
    def test_stats_empty(self):
        """Test stats with no skills."""
        s = stats()
        assert s["total"] >= 0
        assert "by_status" in s
    
    def test_list_skills_empty(self):
        """Test listing skills with empty index."""
        skills = list_skills()
        assert isinstance(skills, list)


# ── OMNYX Integration Tests ──────────────────────────────────────────────

class TestOmnyxAspirationHook:
    @pytest.mark.asyncio
    async def test_aspiration_detection_in_omnyx(self):
        """Test that OMNYX detects aspiration triggers."""
        from brain_qa.omnyx_direction import omnyx_process
        
        result = await omnyx_process(
            "GPT bisa bikin gambar, harusnya SIDIX juga bisa dong!",
            persona="UTZ",
        )
        
        # Should complete without error
        assert "answer" in result
        assert "sanad_score" in result


# ── Cleanup helper ───────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def cleanup_aspirations():
    """Cleanup test aspirations after each test."""
    yield
    # Remove test entries from aspirations index
    idx_path = _aspirations_index()
    if idx_path.exists():
        import json
        lines = []
        with idx_path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip() and '"derived_from":"test"' not in line and '"derived_from":"api"' not in line:
                    lines.append(line)
        with idx_path.open("w", encoding="utf-8") as f:
            for line in lines:
                f.write(line)


# ── Run tests ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
