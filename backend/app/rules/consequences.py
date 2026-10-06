"""'What could happen if you go ahead' lines, looked up per finding id from data/consequences.json."""
import json
from pathlib import Path
from typing import List

from ..models import Finding

MAX_CONSEQUENCES = 3
_SEV_ORDER = {"high": 0, "medium": 1, "low": 2}

_RAW = json.loads((Path(__file__).parent / "data" / "consequences.json").read_text(encoding="utf-8"))
CONSEQUENCES = _RAW["consequences"]
NO_CONSEQUENCE = set(_RAW["no_consequence"])


def build_consequences(findings: List[Finding], verdict: str, lang: str) -> List[str]:
    """Up to 3 lines, most serious first, de-duplicated. Empty for Safe or when no finding has an entry."""
    if verdict == "safe":
        return []
    entries = [(CONSEQUENCES[f.id], i) for i, f in enumerate(findings) if f.id in CONSEQUENCES]
    entries.sort(key=lambda e: (_SEV_ORDER[e[0]["severity"]], e[1]))
    out: List[str] = []
    for entry, _ in entries:
        text = entry.get(lang) or entry["en"]
        if text not in out:
            out.append(text)
        if len(out) == MAX_CONSEQUENCES:
            break
    return out
