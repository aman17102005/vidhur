"""Domain / URL checks: lookalikes, shorteners, odd structure. Purely string-based, never touches the network."""
import ipaddress
import json
import re
from pathlib import Path
from typing import List, Optional, Tuple

from ..models import Finding
from .extract import TLD, ParsedUrl

_DATA = Path(__file__).parent / "data"


def _load(name):
    with open(_DATA / name, encoding="utf-8") as f:
        return json.load(f)


BRANDS = _load("brands.json")
SHORTENERS = set(_load("shorteners.json"))
RISKY_TLDS = set(_load("risky_tlds.json"))
FREE_HOSTS = set(_load("free_hosts.json"))
OFFICIAL = {d for b in BRANDS for d in b["official"]}
TRUSTED_SUFFIXES = {"gov.in", "nic.in", "ac.in", "edu.in", "res.in", "gov"}
GOV_WORDS = {"gov", "govt", "government", "ministry", "scholarship", "scholarships", "yojana"}
FREE_MAIL = {"gmail.com", "yahoo.com", "yahoo.in", "outlook.com", "hotmail.com", "rediffmail.com", "proton.me", "protonmail.com", "ymail.com", "live.com"}
URL_BAIT_WORDS = re.compile(r"(login|log-in|signin|verify|verification|kyc|otp|claim|reward|refund|secure|update|bonus|prize|free|offer|unlock)", re.I)
CHAT_HOSTS = {"wa.me", "t.me", "telegram.me", "telegram.dog", "api.whatsapp.com", "chat.whatsapp.com"}

# Character swaps scammers use to fake a brand name.
_CONFUSABLE_VARIANTS = (
    lambda s: s.replace("rn", "m").replace("vv", "w").replace("0", "o").replace("1", "l").replace("5", "s").replace("3", "e"),
    lambda s: s.replace("rn", "m").replace("vv", "w").replace("0", "o").replace("1", "i").replace("5", "s").replace("3", "e"),
)
_RISK_WORDS = {"kyc", "update", "verify", "login", "secure", "offer", "reward", "scholarship", "internship", "refund", "claim", "pay", "bonus", "support", "care", "helpline", "customer", "account", "alert", "apply", "career", "careers", "jobs", "recruitment", "hiring"}


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def registrable(host: str) -> str:
    ext = TLD(host)
    return getattr(ext, "top_domain_under_public_suffix", None) or ext.registered_domain


def _tokens(label: str) -> List[str]:
    out = set(re.findall(r"[a-z]+|\d+", label))
    out.update(t for t in label.split("-") if t)
    return list(out)


def _brand_match(label: str, is_main_label: bool) -> Optional[Tuple[dict, str, str]]:
    """Return (brand, kind, matched_token) where kind is 'typo' or 'name'."""
    tokens = _tokens(label)
    for brand in BRANDS:
        for bt in brand["tokens"]:
            # 1. brand name used as a whole word in the label (sbi-kyc.com, paytm.login.xyz)
            if bt in tokens:
                return brand, "name", bt
            # 2. long brand names glued to extra words (paytmoffers.com)
            if len(bt) >= 5 and bt in label:
                return brand, "name", bt
            if not is_main_label or len(bt) < 5:
                continue
            # 3. typos and character swaps (paytrn, hdfcbamk, amaz0n)
            for tok in tokens + [label]:
                if tok == bt:
                    continue
                if any(v(tok) == bt for v in _CONFUSABLE_VARIANTS):  # tok != bt, so a swap was needed
                    return brand, "typo", bt
                limit = 1 if len(bt) <= 7 else 2
                if abs(len(tok) - len(bt)) <= limit and levenshtein(tok, bt) <= limit:
                    return brand, "typo", bt
    return None


def check_host(host: str, *, explicit_http: bool = False) -> Tuple[List[Finding], bool]:
    """Return (findings, is_official)."""
    out: List[Finding] = []
    host = host.lower().rstrip(".")

    try:
        ipaddress.ip_address(host.strip("[]"))
        return [Finding(id="ip_host", severity="medium", action="bad_link", evidence=host,
                        reason="The link goes to a raw number address instead of a real website name. Real services do not do this.")], False
    except ValueError:
        pass

    if any(ord(c) > 127 for c in host) or "xn--" in host:
        out.append(Finding(id="lookalike_chars", severity="high", action="bad_link", evidence=host,
                           reason="The web address uses special look-alike characters (for example a Cyrillic 'а' that looks like an English 'a') to impersonate a real site."))

    ext = TLD(host)
    if not ext.suffix:
        return out, False
    reg = registrable(host)

    if reg in CHAT_HOSTS or host in CHAT_HOSTS:
        out.append(Finding(id="move_to_chat_link", severity="low", action="verify", evidence=host,
                           reason="The link opens a WhatsApp or Telegram chat. Scammers move conversations there to avoid official records."))
        return out, True

    if reg in OFFICIAL or host in OFFICIAL or ext.suffix in TRUSTED_SUFFIXES:
        return out, True

    if reg in SHORTENERS:
        out.append(Finding(id="shortener", severity="medium", action="bad_link", evidence=host,
                           reason=f"This is a shortened link ({reg}). It hides the real destination, and Vidhur cannot verify where it leads."))
        return out, False

    if reg in FREE_HOSTS:
        out.append(Finding(id="free_hosting", severity="low", action="bad_link", evidence=host,
                           reason="The page is on a free website-builder address. Anyone can create these in minutes, and scam pages often use them."))

    labels = [l for l in ((ext.subdomain + "." if ext.subdomain else "") + ext.domain).split(".") if l]
    brand_hit = None
    for i, label in enumerate(reversed(labels)):  # main label first
        brand_hit = _brand_match(label, is_main_label=(i == 0))
        if brand_hit:
            break
    if brand_hit:
        brand, kind, tok = brand_hit
        official = brand["official"][0]
        if kind == "typo":
            reason = f"'{host}' looks like {brand['name']} but is spelled slightly differently. The real site is {official}. This is a classic fake-site trick."
        else:
            reason = f"'{host}' uses the name {brand['name']} but is not their real website (that is {official}). Scammers add the brand name to look genuine."
        out.append(Finding(id="lookalike_domain", severity="high", action="bad_link", evidence=host, reason=reason))
    elif GOV_WORDS & set(_tokens(ext.domain) + [t for l in ext.subdomain.split(".") for t in _tokens(l)]):
        out.append(Finding(id="fake_gov", severity="medium", action="bad_link", evidence=host,
                           reason="The web address sounds official (government or scholarship), but it does not end in .gov.in or .nic.in. Real Indian government sites do."))

    tld = ext.suffix.split(".")[-1]
    if tld in RISKY_TLDS:
        out.append(Finding(id="risky_tld", severity="low", action="bad_link", evidence=host,
                           reason=f"The address ends in .{tld}, an ending that is cheap and very common on scam sites."))

    if ext.domain.count("-") >= 3 or len(host) > 40 or ext.subdomain.count(".") >= 2:
        out.append(Finding(id="odd_structure", severity="low", action="bad_link", evidence=host,
                           reason="The web address is unusually long or has many parts, which is a common way to hide who really owns it."))
    return out, False


def check_url(u: ParsedUrl) -> List[Finding]:
    out: List[Finding] = []
    if u.has_userinfo:
        out.append(Finding(id="url_at_trick", severity="high", action="bad_link", evidence=u.raw[:80],
                           reason="The link contains an '@' sign. Everything before it is ignored by the browser, so the real destination is hidden behind a fake-looking name."))

    findings, official = check_host(u.host)
    out.extend(findings)

    if u.scheme == "http":
        out.append(Finding(id="no_https", severity="low", action="bad_link", evidence=u.raw[:80],
                           reason="The link is not encrypted (http, not https). Never enter personal details on such a page."))

    path = (u.path or "").lower()
    if path.endswith(".apk"):
        out.append(Finding(id="apk_install", severity="high", action="bad_app", evidence=u.raw[:80],
                           reason="The link downloads an APK file (an Android app outside the Play Store). Fake apps can read your SMS and steal OTPs."))

    is_form = (u.host in {"docs.google.com", "forms.google.com"} and path.startswith("/forms")) or u.host == "forms.gle"
    if is_form:
        out.append(Finding(id="form_collect", severity="low", action="verify", evidence=u.host,
                           reason="The link is a Google Form. Scammers use forms to collect your details. Official bodies mostly use their own portals."))

    if not official and URL_BAIT_WORDS.search(path + "?" + u.query):
        out.append(Finding(id="url_bait_words", severity="low", action="bad_link", evidence=(u.host + u.path)[:80],
                           reason="The link has words like 'login', 'verify', 'kyc' or 'claim' on a site that is not an official one."))
    return out


def check_mismatch(display: str, href: str) -> List[Finding]:
    from .extract import _find_urls, parse_url  # local import to avoid cycle at module load

    real = parse_url(href)
    if not real:
        return []
    shown = _find_urls(display)
    for s in shown:
        if registrable(s.host) and registrable(real.host) and registrable(s.host) != registrable(real.host):
            return [Finding(id="link_mismatch", severity="high", action="bad_link", evidence=f"{s.host} → {real.host}",
                            reason=f"The link text says '{s.host}' but it actually goes to '{real.host}'. This is a common trick to make a fake link look real.")]
    return []


def check_email_domain(domain: str) -> List[Finding]:
    if domain in FREE_MAIL:
        return []
    findings, _ = check_host(domain)
    return [f for f in findings if f.id in {"lookalike_domain", "lookalike_chars", "fake_gov"}]
