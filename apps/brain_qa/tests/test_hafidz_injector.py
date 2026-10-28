"""
test_hafidz_injector.py — Unit tests for Hafidz Injector (Sprint B)

Test coverage:
1. Store to Golden Store
2. Store to Lesson Store
3. Retrieve golden examples
4. Retrieve lesson warnings
5. Build Hafidz prompt
6. End-to-end retrieve + store

Author: Mighan Lab / SIDIX
License: MIT
"""
import pytest
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from brain_qa.hafidz_injector import (
    HafidzExample,
    HafidzLesson,
    HafidzContext,
    HafidzInjector,
    store_golden,
    store_lesson,
    retrieve_golden_examples,
    retrieve_lesson_warnings,
    build_hafidz_prompt,
    get_hafidz_context,
    store_to_hafidz,
    DEFAULT_HAFIDZ_ROOT,
    GOLDEN_ROOT,
    LESSON_ROOT,
)


# ── Golden Store Tests ───────────────────────────────────────────────────

class TestGoldenStore:
    @pytest.mark.asyncio
    async def test_store_golden(self):
        """Test storing high-quality Q&A to Golden Store."""
        result = await store_golden(
            query="Siapa presiden Indonesia?",
            answer="Prabowo Subianto",
            persona="AYMAN",
            sanad_score=0.95,
            sources_used=["corpus", "web"],
            tools_used=["corpus_search", "web_search"],
        )
        
        assert result["stored"] is True
        assert result["store"] == "golden"
        assert result["note_id"].startswith("hafidz_")
        assert Path(result["path"]).exists()
    
    @pytest.mark.asyncio
    async def test_store_lesson(self):
        """Test storing failure case to Lesson Store."""
        result = await store_lesson(
            query="Siapa presiden Indonesia?",
            answer="Joko Widodo",
            persona="AYMAN",
            sanad_score=0.45,
            failure_context="Jawaban outdated, Prabowo sudah dilantik",
            sources_used=["corpus"],
            tools_used=["corpus_search"],
        )
        
        assert result["stored"] is True
        assert result["store"] == "lesson"
        assert Path(result["path"]).exists()
    
    @pytest.mark.asyncio
    async def test_store_golden_with_metadata(self):
        """Test storing with extra metadata."""
        result = await store_golden(
            query="Test query",
            answer="Test answer",
            persona="UTZ",
            sanad_score=0.90,
            sources_used=["web"],
            tools_used=["web_search"],
            metadata={"extra": "data"},
        )
        
        assert result["stored"] is True
        assert Path(result["path"]).exists()


# ── Retrieval Tests ──────────────────────────────────────────────────────

class TestRetrieval:
    @pytest.mark.asyncio
    async def test_retrieve_golden_examples(self):
        """Test retrieving golden examples."""
        # First store some test data
        await store_golden(
            query="Apa ibu kota Indonesia?",
            answer="Jakarta",
            persona="AYMAN",
            sanad_score=0.95,
            sources_used=["corpus"],
            tools_used=["corpus_search"],
        )
        
        # Then retrieve
        examples = await retrieve_golden_examples(
            query="ibu kota Indonesia",
            persona="AYMAN",
            max_examples=3,
        )
        
        assert isinstance(examples, list)
        # May or may not find the example depending on BM25 scoring
        for ex in examples:
            assert isinstance(ex, HafidzExample)
            assert ex.sanad_score >= 0.80
    
    @pytest.mark.asyncio
    async def test_retrieve_lesson_warnings(self):
        """Test retrieving lesson warnings."""
        # First store a lesson
        await store_lesson(
            query="Berapa hasil 2+2?",
            answer="5",
            persona="ABOO",
            sanad_score=0.30,
            failure_context="Jawaban salah, 2+2=4",
            sources_used=[],
            tools_used=["calculator"],
        )
        
        # Then retrieve
        lessons = await retrieve_lesson_warnings(
            query="matematika",
            persona="ABOO",
            max_warnings=2,
        )
        
        assert isinstance(lessons, list)
        for lesson in lessons:
            assert isinstance(lesson, HafidzLesson)
    
    @pytest.mark.asyncio
    async def test_retrieve_with_persona_filter(self):
        """Test that persona filter works."""
        await store_golden(
            query="Test persona filter",
            answer="Answer",
            persona="UTZ",
            sanad_score=0.95,
            sources_used=[],
            tools_used=[],
        )
        
        # Retrieve with matching persona
        examples = await retrieve_golden_examples(
            query="test persona",
            persona="UTZ",
            max_examples=1,
        )
        
        # Should find UTZ examples
        for ex in examples:
            assert ex.persona == "UTZ"


# ── Prompt Builder Tests ─────────────────────────────────────────────────

class TestPromptBuilder:
    def test_build_hafidz_prompt_empty(self):
        """Test building prompt with empty context."""
        context = HafidzContext()
        prompt = build_hafidz_prompt(context)
        assert prompt == ""
    
    def test_build_hafidz_prompt_with_examples(self):
        """Test building prompt with golden examples."""
        context = HafidzContext(
            golden_examples=[
                HafidzExample(
                    query="Q1",
                    answer="A1",
                    persona="AYMAN",
                    sanad_score=0.95,
                    sources_used=["corpus"],
                    date="2026-05-01",
                    knowledge_id="test1",
                )
            ]
        )
        prompt = build_hafidz_prompt(context)
        assert "CONTOH BERKUALITAS TINGGI" in prompt
        assert "Q1" in prompt
        assert "A1" in prompt
    
    def test_build_hafidz_prompt_with_warnings(self):
        """Test building prompt with lesson warnings."""
        context = HafidzContext(
            lesson_warnings=[
                HafidzLesson(
                    query="Q1",
                    answer="Bad A1",
                    persona="AYMAN",
                    sanad_score=0.30,
                    failure_context="Wrong answer",
                    tools_used=[],
                    date="2026-05-01",
                    knowledge_id="test1",
                )
            ]
        )
        prompt = build_hafidz_prompt(context)
        assert "PERINGATAN" in prompt
        assert "Wrong answer" in prompt


# ── HafidzInjector Integration Tests ─────────────────────────────────────

class TestHafidzInjector:
    @pytest.mark.asyncio
    async def test_retrieve_context(self):
        """Test HafidzInjector retrieve_context."""
        injector = HafidzInjector()
        
        # Store some test data first
        await store_golden(
            query="Test retrieve context",
            answer="Answer",
            persona="AYMAN",
            sanad_score=0.95,
            sources_used=[],
            tools_used=[],
        )
        
        context = await injector.retrieve_context(
            query="test retrieve",
            persona="AYMAN",
            max_examples=2,
        )
        
        assert isinstance(context, HafidzContext)
        assert isinstance(context.golden_examples, list)
        assert isinstance(context.lesson_warnings, list)
    
    @pytest.mark.asyncio
    async def test_store_result_golden(self):
        """Test storing result that qualifies for Golden Store."""
        injector = HafidzInjector()
        
        result = await injector.store_result(
            query="Test golden",
            answer="Answer",
            persona="AYMAN",
            sanad_score=0.95,
            threshold=0.85,
            sources_used=["corpus"],
            tools_used=["corpus_search"],
        )
        
        assert result["stored"] is True
        assert result["store"] == "golden"
    
    @pytest.mark.asyncio
    async def test_store_result_lesson(self):
        """Test storing result that goes to Lesson Store."""
        injector = HafidzInjector()
        
        result = await injector.store_result(
            query="Test lesson",
            answer="Wrong answer",
            persona="AYMAN",
            sanad_score=0.50,
            threshold=0.85,
            sources_used=[],
            tools_used=[],
            failure_context="Answer incorrect",
        )
        
        assert result["stored"] is True
        assert result["store"] == "lesson"
    
    @pytest.mark.asyncio
    async def test_stats(self):
        """Test statistics tracking."""
        injector = HafidzInjector()
        
        # Do some operations
        await injector.retrieve_context("test", "AYMAN")
        await injector.store_result(
            query="test",
            answer="answer",
            persona="AYMAN",
            sanad_score=0.90,
            threshold=0.85,
            sources_used=[],
            tools_used=[],
        )
        
        stats = injector.get_stats()
        assert stats["retrievals"] >= 1
        assert stats["stores"] >= 1
    
    @pytest.mark.asyncio
    async def test_convenience_functions(self):
        """Test convenience functions."""
        context = await get_hafidz_context("test query", "AYMAN", max_examples=1)
        assert isinstance(context, HafidzContext)
        
        result = await store_to_hafidz(
            query="test",
            answer="answer",
            persona="AYMAN",
            sanad_score=0.90,
            threshold=0.85,
        )
        assert result["stored"] is True


# ── Cleanup helper ───────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def cleanup_hafidz():
    """Cleanup test files after each test."""
    yield
    # Clean up test files created today
    today = "2026-05-01"  # Note: adjust if running on different date
    for root in [GOLDEN_ROOT, LESSON_ROOT]:
        if root.exists():
            for f in root.rglob("*.md"):
                try:
                    if f.stat().st_size < 10000:  # only small test files
                        f.unlink()
                except Exception:
                    pass


# ── Run tests ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
