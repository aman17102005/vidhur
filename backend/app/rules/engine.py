"""Deterministic rule engine. Always runs first and alone produces the verdict."""
import re
from typing import List

from ..models import AnalysisResult, Finding, MAX_CONTENT_CHARS
from .domains import FREE_MAIL, check_email_domain, check_mismatch, check_url
from .extract import extract_entities
from .patterns import run_phrase_rules

_SEV_ORDER = {"high": 0, "medium": 1, "low": 2}
_ACTION_ORDER = ["share_info", "remote", "bad_app", "qr_pay", "upi_confirm", "pay_fee", "bad_link", "verify"]
_OPP_WORDS = re.compile(r"\b(?:internship|recruit\w*|hr\b|hiring|offer letter|placement|job|career)", re.I)
_MAX_PER_ID = 2

NEXT_STEPS = {
    "share_info": "Do not share this. Banks, colleges and companies never ask for OTP, PIN, CVV or passwords by message or call. Ignore the message and do not reply.",
    "remote": "Do not install the app or share your screen. Anyone who asks for this can empty your bank account. Block the sender.",
    "bad_app": "Do not install this app or file. Install apps only from the Play Store or App Store, and only ones you went looking for yourself.",
    "qr_pay": "Do not scan or approve anything. You never need to scan a QR code or enter your UPI PIN to receive money. Scan only when you want to pay someone.",
    "upi_confirm": "Scanning this will send a payment from your account. Check that the recipient name shown in your UPI app is exactly who you mean to pay before you enter your PIN. If you were told this is to receive money, stop: receiving never needs a scan or PIN.",
    "pay_fee": "Do not pay anything. Verify the offer yourself: use the official website, or ask your college placement cell or scholarship office. Genuine offers do not charge a fee.",
    "bad_link": "Do not click this link or enter any details on it. If you think it may be real, type the official website address yourself or use the official app.",
    "verify": "Be careful. Check directly with the organisation using a phone number or website you found yourself, not one from this message. Do not act under pressure.",
}
SAFE_STEP = "No known scam signs found. That does not guarantee it is safe. If money or personal details are involved, confirm with the sender through an official channel first."
REPORT_HINT = "If you lost money or shared details, call 1930 (national cybercrime helpline) at once and report at cybercrime.gov.in. Tell your bank to block the card or UPI."


def _shouting_finding(text: str) -> List[Finding]:
    letters = [c for c in text if c.isalpha() and c.isascii()]
    caps_ratio = sum(c.isupper() for c in letters) / len(letters) if letters else 0
    if (len(letters) >= 40 and caps_ratio > 0.6) or text.count("!") >= 4:
        return [Finding(id="shouting", severity="low", action="verify", evidence=None,
                        reason="The message is written in ALL CAPS or with many '!!!'. Scam messages often shout to create panic.")]
    return []


def _upi_findings(ent) -> List[Finding]:
    out = []
    for u in ent.upi:
        who = u.payee_name or u.payee_vpa or "an unknown payee"
        amt = f" for ₹{u.amount}" if u.amount else ""
        out.append(Finding(id="upi_pay_qr", severity="medium", action="upi_confirm", evidence=(u.payee_vpa or u.raw)[:80],
                           reason=f"This is a UPI payment code. Scanning it will send a payment from your account to {who}{amt}. Confirm the recipient name first, and never scan one to 'receive' money."))
    return out


def _dedupe_and_sort(findings: List[Finding]) -> List[Finding]:
    counts, kept = {}, []
    for f in findings:
        counts[f.id] = counts.get(f.id, 0) + 1
        if counts[f.id] <= _MAX_PER_ID:
            kept.append(f)
    kept.sort(key=lambda f: _SEV_ORDER[f.severity])
    return kept


def _verdict(findings: List[Finding]) -> str:
    n = {s: sum(f.severity == s for f in findings) for s in _SEV_ORDER}
    if n["high"] >= 1 or n["medium"] >= 2:
        return "high_risk"
    if n["medium"] == 1 or n["low"] >= 2:
        return "suspicious"
    return "safe"


def _next_step(findings: List[Finding], verdict: str) -> str:
    if verdict == "safe":
        return SAFE_STEP
    relevant = [f for f in findings if f.severity != "low"] or findings
    best = min(relevant, key=lambda f: (_SEV_ORDER[f.severity], _ACTION_ORDER.index(f.action) if f.action in _ACTION_ORDER else 99))
    return NEXT_STEPS.get(best.action, NEXT_STEPS["verify"])


def analyze(content: str) -> AnalysisResult:
    text = content[:MAX_CONTENT_CHARS]
    ent = extract_entities(text)
    findings: List[Finding] = []

    for u in ent.urls:
        findings += check_url(u)
    for display, href in ent.display_pairs:
        findings += check_mismatch(display, href)
    for dom in ent.emails:
        findings += check_email_domain(dom)
    if any(d in FREE_MAIL for d in ent.emails) and _OPP_WORDS.search(text):
        findings.append(Finding(id="freemail_company", severity="low", action="verify",
                                evidence=next(d for d in ent.emails if d in FREE_MAIL),
                                reason="A job or internship contact uses a free email address (like Gmail). Real companies use their own company email."))
    findings += _upi_findings(ent)
    findings += run_phrase_rules(text)
    findings += _shouting_finding(text)

    findings = _dedupe_and_sort(findings)
    verdict = _verdict(findings)
    return AnalysisResult(
        verdict=verdict,
        findings=findings,
        next_step=_next_step(findings, verdict),
        report_hint=REPORT_HINT if verdict == "high_risk" else None,
    )
