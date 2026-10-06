import re
from pathlib import Path

import pytest

from app.rules.consequences import CONSEQUENCES, MAX_CONSEQUENCES, NO_CONSEQUENCE
from app.rules.engine import analyze
from app.rules.patterns import RULES

RULES_DIR = Path(__file__).parents[1] / "app" / "rules"
LANGS = ("en", "hi", "hinglish")


def all_finding_ids():
    """Every finding id the engine can emit: phrase rules from JSON plus ids created in Python code."""
    ids = {r.id for r in RULES}
    for py in RULES_DIR.glob("*.py"):
        ids |= set(re.findall(r'Finding\(\s*id="([a-z_]+)"', py.read_text(encoding="utf-8")))
    return ids


def test_every_finding_id_has_a_consequence_or_is_explicitly_exempt():
    ids = all_finding_ids()
    assert len(ids) > 40  # guards against the scan silently finding nothing
    missing = sorted(ids - set(CONSEQUENCES) - NO_CONSEQUENCE)
    assert not missing, f"Add these to consequences.json (entry) or its no_consequence list: {missing}"


def test_no_stale_entries_and_no_overlap():
    ids = all_finding_ids()
    assert not (set(CONSEQUENCES) | NO_CONSEQUENCE) - ids, "consequences.json mentions ids that no rule emits"
    assert not set(CONSEQUENCES) & NO_CONSEQUENCE


@pytest.mark.parametrize("fid", sorted(CONSEQUENCES))
def test_entry_has_all_languages_and_careful_wording(fid):
    e = CONSEQUENCES[fid]
    assert e["severity"] in {"high", "medium"}
    for lang in LANGS:
        assert e[lang].strip(), (fid, lang)
    # careful wording: hedged, never a flat promise of certainty
    assert not re.search(r"\b(definitely|certainly|always|never fail|100%)\b", e["en"], re.I), e["en"]


def test_safe_result_has_no_consequences():
    assert analyze("Hey, are we meeting at 5 for the project discussion?").consequences == []


def test_high_risk_has_at_most_three_and_no_duplicates():
    r = analyze("Dear customer your account will be blocked. Update KYC now http://sbi-kyc-update.xyz Share your OTP and send your PIN. Pay Rs 500 registration fee for internship")
    assert r.verdict == "high_risk"
    assert 1 <= len(r.consequences) <= MAX_CONSEQUENCES
    assert len(set(r.consequences)) == len(r.consequences)
    sev = {e[lang]: e["severity"] for e in CONSEQUENCES.values() for lang in ("en",)}
    order = [{"high": 0, "medium": 1}[sev[c]] for c in r.consequences]
    assert order == sorted(order)  # most serious first
    assert sev[r.consequences[0]] == "high"


def test_consequence_language_follows_the_message():
    assert "samne wala" in analyze("Aapka OTP batao turant warna account band ho jayega").consequences[0]
    assert "सामने वाला" in analyze("अपना ओटीपी बताओ और पैसे भेजो").consequences[0]
    assert analyze("share your OTP").language == "en"


def test_finding_with_no_entry_shows_nothing_rather_than_inventing():
    r = analyze("check this https://mysite.xyz/offer")  # only low, exempt findings
    assert r.consequences == []
