"""Scam playbooks: names a known scam type and explains how it works. Data lives in data/playbooks.json."""
import json
import re
from pathlib import Path
from typing import List, Optional

from ..models import Finding, Playbook

# A playbook needs at least this many of its finding ids to fire before it is shown.
PLAYBOOK_MIN_MATCHES = 2

_RAW = json.loads((Path(__file__).parent / "data" / "playbooks.json").read_text(encoding="utf-8"))
PLAYBOOKS = _RAW["playbooks"]


def match_playbook(findings: List[Finding], text: str, verdict: str, lang: str) -> Optional[Playbook]:
    """Best single playbook, or None. Never returned for Safe results."""
    if verdict == "safe":
        return None
    fired = {f.id for f in findings}
    lowered = text.lower()
    best, best_key = None, None
    for pb in PLAYBOOKS:
        hits = len(fired & set(pb["finding_ids"]))
        if hits < PLAYBOOK_MIN_MATCHES:
            continue
        boost = sum(1 for term in pb.get("boost_terms", []) if re.search(r"\b" + re.escape(term), lowered))
        key = (hits, boost)  # more matching rules wins; message wording breaks ties
        if best_key is None or key > best_key:
            best, best_key = pb, key
    if best is None:
        return None
    pick = lambda d: d.get(lang) or d["en"]
    return Playbook(
        id=best["id"],
        name=pick(best["name"]),
        how_it_works=pick(best["how_it_works"]),
        what_next=pick(best["what_next"]),
        real_looks_like=pick(best["real_looks_like"]),
    )
