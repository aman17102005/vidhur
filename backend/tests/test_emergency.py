import json
import re
from datetime import date
from pathlib import Path

import pytest

FRONTEND = Path(__file__).parents[2] / "frontend"
FILE = FRONTEND / "src" / "data" / "emergency.json"
pytestmark = pytest.mark.skipif(not FILE.exists(), reason="frontend folder not present")

LANGS = ("en", "hi", "hinglish")
DATA = json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}


def test_last_verified_is_a_real_past_date():
    assert date.fromisoformat(DATA["last_verified"]) <= date.today()
    assert DATA["verified_from"] and all(v["url"].startswith("https://") for v in DATA["verified_from"])


def test_contacts_are_not_empty_and_are_well_formed():
    h, p = DATA["contacts"]["helpline"], DATA["contacts"]["portal"]
    assert h["number"].strip() and h["tel"] == "tel:" + h["number"]
    assert re.fullmatch(r"\d{4,}", h["number"])
    assert p["url"].startswith("https://") and p["display"].strip()
    for lang in LANGS:
        assert h["label"][lang].strip() and p["label"][lang].strip()


def test_every_case_returns_steps_in_all_three_languages():
    assert set(DATA["cases"]) == {"paid", "otp", "link", "details"}
    for cid, case in DATA["cases"].items():
        assert len(case["steps"]) >= 4, cid
        for lang in LANGS:
            assert case["title"][lang].strip(), (cid, lang)
            for sid in case["steps"]:
                assert DATA["steps"][sid][lang].strip(), (cid, sid, lang)


def test_required_advice_is_present_in_the_right_cases():
    s = DATA["cases"]
    assert "call_bank_money" in s["paid"]["steps"] and "no_recovery" in s["paid"]["steps"]
    assert "change_pins" in s["otp"]["steps"]
    assert {"airplane_uninstall", "change_passwords_other_device"} <= set(s["link"]["steps"])
    for case in s.values():  # every case: report to 1930 and keep evidence
        assert "call_1930" in case["steps"] and "keep_evidence" in case["steps"]
    for lang in LANGS:
        assert "1930" in DATA["steps"]["call_1930"][lang]
        assert "1930" in DATA["disclaimer"][lang]


def test_no_unverified_phone_numbers_anywhere_in_the_file():
    blob = FILE.read_text(encoding="utf-8")
    numbers = set(re.findall(r"(?<![\d.])\d{4,}(?![\d])", blob)) - {"2026", "2176146"}
    assert numbers == {"1930"}, f"Unexpected number(s) in emergency.json: {numbers - {'1930'}}"
    assert not re.search(r"\b1800[\s-]?\d", blob)


def test_ui_strings_exist_in_all_languages():
    for key, val in DATA["ui"].items():
        for lang in LANGS:
            assert val[lang].strip(), (key, lang)


def test_complaint_helper_code_never_touches_the_network_or_storage():
    sources = "\n".join((FRONTEND / "src" / p).read_text(encoding="utf-8")
                        for p in ("lib/complaint.ts", "components/ComplaintHelper.tsx", "components/EmergencyHelp.tsx"))
    for banned in ("fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket", "localStorage", "sessionStorage", "indexedDB", "console.", "lib/api"):
        assert banned not in sources, banned
    # nothing under src/ may send the pasted complaint text to the server API
    api = (FRONTEND / "src" / "lib" / "api.ts").read_text(encoding="utf-8")
    assert "complaint" not in api.lower() and "emergency" not in api.lower()
