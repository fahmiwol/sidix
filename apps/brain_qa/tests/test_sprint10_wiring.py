"""
test_sprint10_wiring.py — Tests untuk Sprint 10 gap fixes.

Covers:
1. cot_engine: complexity classifier + scaffold generation
2. branch_manager: tool_whitelist + corpus_filter (already tested in test_tiranyx, extra coverage)
3. agent_react: agency_id in signature + AgentSession field
4. agent_serve: ChatRequest.agency_id field
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


# ── 1. CoT Engine ─────────────────────────────────────────────────────────────

class TestCotEngine:
    def setup_method(self):
        from brain_qa.cot_engine import (
            classify_complexity,
            get_cot_scaffold,
            inject_cot_into_prompt,
            get_complexity,
        )
        self.classify = classify_complexity
        self.scaffold = get_cot_scaffold
        self.inject = inject_cot_into_prompt
        self.complexity = get_complexity

    def test_low_greeting(self):
        assert self.classify("halo") == "low"
        assert self.classify("hai") == "low"
        assert self.classify("assalamu alaikum") == "low"

    def test_low_short_question(self):
        assert self.classify("siapa kamu") == "low"

    def test_medium_definition(self):
        assert self.classify("apa itu machine learning?") == "medium"

    def test_medium_explanation(self):
        assert self.classify("jelaskan cara kerja BM25") == "medium"

    def test_high_compare(self):
        assert self.classify("bandingkan arsitektur transformer dan mamba secara mendalam") == "high"

    def test_high_implement(self):
        assert self.classify("implementasi sistem rekomendasi dengan collaborative filtering") == "high"

    def test_high_math(self):
        assert self.classify("hitung 25 * 4 + integral fungsi cos(x)") == "high"

    def test_scaffold_high_utz_nonempty(self):
        scaffold = self.scaffold("bandingkan transformer vs mamba", "UTZ")
        assert len(scaffold) > 50
        assert "Langkah" in scaffold or "langkah" in scaffold.lower() or "sub-masalah" in scaffold

    def test_scaffold_low_empty(self):
        scaffold = self.scaffold("halo", "UTZ")
        assert scaffold == ""

    def test_scaffold_ayman_high(self):
        scaffold = self.scaffold("implementasi sorting algorithm", "AYMAN")
        assert len(scaffold) > 50
        assert "engineering" in scaffold.lower() or "requirement" in scaffold.lower()

    def test_scaffold_unknown_persona_fallback_utz(self):
        # Unknown persona → fallback ke UTZ
        scaffold_unknown = self.scaffold("bandingkan dua pendekatan ini", "UNKNOWN_PERSONA")
        scaffold_utz = self.scaffold("bandingkan dua pendekatan ini", "UTZ")
        assert scaffold_unknown == scaffold_utz

    def test_inject_adds_cot_block(self):
        result = self.inject("Kamu adalah SIDIX.", "bandingkan transformer vs mamba", "UTZ")
        assert "[CoT]" in result
        assert "Kamu adalah SIDIX." in result

    def test_inject_idempotent(self):
        prompt = "Kamu adalah SIDIX. [CoT] sudah ada."
        result = self.inject(prompt, "bandingkan transformer vs mamba", "UTZ")
        assert result.count("[CoT]") == 1  # tidak ditambah lagi

    def test_inject_low_complexity_noop(self):
        result = self.inject("Kamu adalah SIDIX.", "halo", "UTZ")
        assert "[CoT]" not in result  # tidak inject untuk greeting

    def test_get_complexity_api(self):
        assert self.complexity("halo") == "low"
        assert self.complexity("implementasi neural network dari scratch") == "high"


# ── 2. Branch Manager gating ──────────────────────────────────────────────────

class TestBranchManagerGating:
    def setup_method(self):
        from brain_qa.branch_manager import BranchManager
        self.bm = BranchManager()

    def test_default_allows_all_tools(self):
        assert self.bm.is_tool_allowed("", "", "search_corpus") is True
        assert self.bm.is_tool_allowed("", "", "web_search") is True
        assert self.bm.is_tool_allowed("", "", "shell_run") is True

    def test_whitelist_blocks_unlisted_tool(self):
        self.bm.create_branch("test_agency", "test_client", tool_whitelist=["search_corpus", "graph_search"])
        assert self.bm.is_tool_allowed("test_agency", "test_client", "search_corpus") is True
        assert self.bm.is_tool_allowed("test_agency", "test_client", "graph_search") is True
        assert self.bm.is_tool_allowed("test_agency", "test_client", "shell_run") is False
        assert self.bm.is_tool_allowed("test_agency", "test_client", "web_search") is False

    def test_empty_whitelist_allows_all(self):
        self.bm.create_branch("test_agency2", "test_client2", tool_whitelist=[])
        assert self.bm.is_tool_allowed("test_agency2", "test_client2", "any_tool") is True

    def test_corpus_filter_returned(self):
        self.bm.create_branch("test_agency3", "test_client3", corpus_filter=["fiqih", "quran"])
        cf = self.bm.get_corpus_filter("test_agency3", "test_client3")
        assert "fiqih" in cf
        assert "quran" in cf

    def test_default_corpus_filter_empty(self):
        assert self.bm.get_corpus_filter("", "") == []


# ── 3. AgentSession + run_react signature ─────────────────────────────────────

class TestAgentReactSignature:
    def test_agent_session_has_agency_id(self):
        from brain_qa.agent_react import AgentSession
        import dataclasses
        fields = {f.name for f in dataclasses.fields(AgentSession)}
        assert "agency_id" in fields
        assert "client_id" in fields

    def test_run_react_accepts_agency_id(self):
        import inspect
        from brain_qa.agent_react import run_react
        params = inspect.signature(run_react).parameters
        assert "agency_id" in params
        assert "client_id" in params

    def test_agent_session_agency_id_default_empty(self):
        from brain_qa.agent_react import AgentSession
        s = AgentSession(session_id="x", question="q", persona="UTZ")
        assert s.agency_id == ""


# ── 4. ChatRequest agency_id ─────────────────────────────────────────────────

class TestChatRequestAgencyId:
    def test_chat_request_has_agency_id(self):
        from brain_qa.agent_serve import ChatRequest
        fields = ChatRequest.model_fields
        assert "agency_id" in fields

    def test_chat_request_agency_id_defaults_empty(self):
        from brain_qa.agent_serve import ChatRequest
        req = ChatRequest(question="test")
        assert req.agency_id == ""

    def test_chat_request_agency_id_set(self):
        from brain_qa.agent_serve import ChatRequest
        req = ChatRequest(question="test", agency_id="tiranyx", client_id="ayman")
        assert req.agency_id == "tiranyx"
        assert req.client_id == "ayman"
