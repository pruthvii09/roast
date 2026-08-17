import re

_REPEATED_BLANK_LINES = re.compile(r"\n{3,}")
_REPEATED_SPACES = re.compile(r"[ \t]+")


def normalize_text(text: str, *, max_chars: int) -> str:
    """
    Collapses repeated whitespace/blank lines and caps length — the
    "store normalized extracted content" step shared by any processor
    whose raw output can be noisy or arbitrarily large (fetched HTML
    text, GitHub metadata + README). Truncation keeps a trailing marker
    rather than silently cutting off mid-thought.
    """
    collapsed = _REPEATED_SPACES.sub(" ", text)
    collapsed = _REPEATED_BLANK_LINES.sub("\n\n", collapsed)
    collapsed = collapsed.strip()
    if len(collapsed) > max_chars:
        collapsed = collapsed[:max_chars].rstrip() + "\n\n[... content truncated ...]"
    return collapsed
