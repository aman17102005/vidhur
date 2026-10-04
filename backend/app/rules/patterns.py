"""Phrase rules (English, Hinglish, Hindi) loaded from data/phrases.json."""
import json
import re
from pathlib import Path
from typing import List

from ..models import Finding

_RAW = json.loads((Path(__file__).parent / "data" / "phrases.json").read_text(encoding="utf-8"))
_VARS = _RAW["vars"]

# "do not share", "never ask you to share" etc. directly before the matched request = a warning, not a request.
_NEGATION_BEFORE = [
    re.compile(r"(?:do\s*not|don'?t|dont|never|mat|nahi|nahin)\W+(?:(?:ever|please|kabhi|bhi)\W+)?$"),
    re.compile(r"(?:never|not|won'?t|will\s+not)\W+(?:ask|request|call)\w*\W+(?:you\W+)?(?:to\W+|for\W+)?$"),
]
_NEGATION_INSIDE = re.compile(r"\b(?:mat|nahi|nahin|never|not|don'?t)\b")


def _sub(p: str) -> str:
    for k, v in _VARS.items():
        p = p.replace(k, v)
    return p


def _compile(patterns):
    return [re.compile(_sub(p), re.I) for p in patterns]


class Rule:
    def __init__(self, raw: dict):
        self.id = raw["id"]
        self.severity = raw["severity"]
        self.action = raw.get("action", "verify")
        self.reason = raw["reason"]
        self.negatable = raw.get("negatable", False)
        self.any = _compile(raw.get("any", []))
        self.all = [_compile(g) for g in raw.get("all", [])]

    def _negated(self, text: str, m: "re.Match") -> bool:
        before = text[max(0, m.start() - 40): m.start()]
        if any(n.search(before) for n in _NEGATION_BEFORE):
            return True
        return bool(_NEGATION_INSIDE.search(m.group(0)))

    def evaluate(self, text: str):
        """Return evidence string if the rule fires, else None."""
        for rx in self.any:
            for m in rx.finditer(text):
                if self.negatable and self._negated(text, m):
                    continue
                return m.group(0)
        if self.all:
            hits = []
            for group in self.all:
                hit = None
                for rx in group:
                    m = rx.search(text)
                    if m:
                        hit = m.group(0)
                        break
                if hit is None:
                    return None
                hits.append(hit)
            return " + ".join(hits)
        return None


RULES = [Rule(r) for r in _RAW["rules"]]


def normalize(text: str) -> str:
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text.lower())


def run_phrase_rules(text: str) -> List[Finding]:
    norm = normalize(text)
    out: List[Finding] = []
    for rule in RULES:
        ev = rule.evaluate(norm)
        if ev is not None:
            out.append(Finding(id=rule.id, severity=rule.severity, action=rule.action, reason=rule.reason, evidence=ev[:90]))
    return out
