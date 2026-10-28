"""Cache jawaban singkat per (persona, pertanyaan) — mengurangi duplikasi beban RAG."""

from __future__ import annotations

import time
from collections import OrderedDict

_TTL_SEC = 300.0
_MAX = 200
_store: OrderedDict[str, tuple[float, str]] = OrderedDict()


def _key(persona: str, question: str) -> str:
    from .g1_policy import normalize_question_key

    return f"{persona.strip().upper()}::{normalize_question_key(question)}"


def get_cached_answer(persona: str, question: str) -> str | None:
    k = _key(persona, question)
    item = _store.get(k)
    if not item:
        return None
    ts, ans = item
    if time.monotonic() - ts > _TTL_SEC:
        try:
            del _store[k]
        except KeyError:
            pass
        return None
    _store.move_to_end(k)
    return ans


def set_cached_answer(persona: str, question: str, answer: str) -> None:
    if not answer or len(answer) < 20:
        return
    k = _key(persona, question)
    while len(_store) >= _MAX:
        _store.popitem(last=False)
    _store[k] = (time.monotonic(), answer)
    _store.move_to_end(k)
