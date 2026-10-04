import json
from pathlib import Path

import pytest

from app.rules.engine import analyze
from app.rules.patterns import RULES

SAFE = [
    "123456 is your OTP for txn of Rs 500 at Amazon. Do not share this with anyone.",
    "Never share your OTP, PIN or password with anyone. Banks will never ask you for them.",
    "SBI never asks you to share OTP or CVV. Stay alert.",
    "Hey, are we meeting at 5 for the project discussion? Library is closed on Sunday.",
    "Your internal exam results are out. Check at https://mycollege.ac.in/results",
    "https://www.sbi.co.in/web/personal-banking",
    "https://internshala.com/internships/computer-science-internship",
    "Please pay the exam fee of Rs 500 at the college accounts office counter.",
    "github.com/torvalds/linux",
]

HIGH = {
    "kyc + lookalike link": "Dear customer your SBI account will be blocked today. Update KYC now http://sbi-kyc-update.xyz/login",
    "fee internship": "Congratulations! You are selected for internship at TCS. Pay Rs 999 registration fee (refundable) to confirm.",
    "otp request": "Sir please share your OTP to verify your account",
    "otp hinglish": "Aapka OTP batao turant warna account band ho jayega",
    "pin to receive": "To receive Rs 5000 refund scan this QR and enter your UPI PIN",
    "anydesk": "Install AnyDesk and tell me the 9 digit code so I can help with your refund",
    "task scam": "Part time job! Complete simple tasks like rate hotels on Google Maps and earn Rs 3000 per day.",
    "typo domain": "https://paytrn.com/offers",
    "swap domain": "http://hdfcbamk.com/netbanking",
    "brand in subdomain": "https://sbi.co.in.secure-login.com",
    "punycode": "https://xn--sbi-9ra.com",
    "at trick": "http://sbi.co.in@evil-site.top/login",
    "html mismatch": '<a href="http://evil-site.top/x">www.sbi.co.in</a>',
    "markdown mismatch": "[www.hdfcbank.com](http://hdfc-secure.top/login)",
    "apk": "Download KYC.apk from this link to complete verification",
    "devanagari otp": "अपना ओटीपी तुरंत भेजो",
}

SUSPICIOUS = {
    "shortener": "check this https://bit.ly/3xYzAbC",
    "ip link": "http://192.168.4.7/offer",
}


@pytest.mark.parametrize("text", SAFE)
def test_safe(text):
    r = analyze(text)
    assert r.verdict == "safe", [f.id for f in r.findings]


@pytest.mark.parametrize("name", HIGH)
def test_high(name):
    r = analyze(HIGH[name])
    assert r.verdict == "high_risk", (name, [f.id for f in r.findings])
    assert r.report_hint


@pytest.mark.parametrize("name", SUSPICIOUS)
def test_suspicious(name):
    r = analyze(SUSPICIOUS[name])
    assert r.verdict in {"suspicious", "high_risk"}, (name, [f.id for f in r.findings])


def test_upi_qr_is_suspicious_by_default():
    r = analyze("upi://pay?pa=shop@ybl&pn=Sharma%20Stores&am=120&cu=INR")
    assert r.verdict == "suspicious"
    f = next(f for f in r.findings if f.id == "upi_pay_qr")
    assert "send a payment" in f.reason and "Sharma Stores" in f.reason and "recipient name" in f.reason
    assert "recipient name" in r.next_step


def test_upi_qr_with_receive_scam_text_is_high_risk():
    r = analyze("Scan this QR to receive Rs 5000 upi://pay?pa=x@ybl&pn=Ravi")
    assert r.verdict == "high_risk"


def test_next_step_matches_worst_issue():
    assert "Do not share" in analyze("share your OTP now").next_step
    assert "Do not pay" in analyze("Pay Rs 500 registration fee to confirm your internship").next_step


def test_no_numeric_scores_in_output():
    r = analyze("Share your OTP").model_dump()
    assert "score" not in json.dumps(r).lower()


def test_all_rules_compile_and_have_ids():
    ids = [r.id for r in RULES]
    assert len(ids) == len(set(ids)) and len(ids) > 20


def test_regex_performance_on_long_input():
    import time
    t = time.time()
    analyze(("share the account number and the " * 400)[:10_000])
    assert time.time() - t < 2
