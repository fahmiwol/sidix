from __future__ import annotations

from dataclasses import dataclass

from .hadith_validate import validate_hadith


@dataclass(frozen=True)
class ValidateTextOptions:
    profile: str  # "generic" | "hadith"
    k: int
    max_snippet_chars: int
    min_overlap_ratio: float
    arabic_normalize: bool
    popular_snippet_max_tokens: int
    popular_snippet_min_strong: int


def validate_text(
    *,
    text: str,
    index_dir_override: str | None,
    opts: ValidateTextOptions,
) -> str:
    profile = opts.profile.strip().lower()

    # Profile determines header subtitle; core logic is shared.
    profile_label = "generic"
    if profile in {"hadith", "hadits"}:
        profile_label = "hadith"

    return validate_hadith(
        hadith_text=text,
        index_dir_override=index_dir_override,
        k=opts.k,
        max_snippet_chars=opts.max_snippet_chars,
        min_overlap_ratio=opts.min_overlap_ratio,
        arabic_normalize=opts.arabic_normalize,
        popular_snippet_max_tokens=opts.popular_snippet_max_tokens,
        popular_snippet_min_strong=opts.popular_snippet_min_strong,
        _profile_label=profile_label,
    )
