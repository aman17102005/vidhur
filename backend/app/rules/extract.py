"""Pull links, e-mail addresses, UPI links and (display text, href) pairs out of free text.

Nothing here touches the network.
"""
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from urllib.parse import parse_qs, urlsplit

import tldextract

# Bundled public-suffix snapshot only: no network fetch, no on-disk cache.
TLD = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None)

_TOKEN_SPLIT = re.compile(r"[^\s<>\"'()\[\]{},;|]+")
_BARE_DOMAIN = re.compile(r"^[a-z0-9][a-z0-9\-\.]*\.[a-z]{2,}(?:[:/?#].*)?$", re.I)
_EMAIL = re.compile(r"[\w.+\-]+@([\w\-]+(?:\.[\w\-]+)+)", re.I)
_HTML_LINK = re.compile(r"<a\s[^>]*?href\s*=\s*[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", re.I | re.S)
_MD_LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", re.I)
_TRAIL = ".,;:!?"


@dataclass
class ParsedUrl:
    raw: str
    scheme: str  # "" when the user gave a bare domain
    host: str
    path: str
    query: str
    has_userinfo: bool


@dataclass
class UpiLink:
    raw: str
    payee_vpa: str
    payee_name: str
    amount: str
    note: str


@dataclass
class Entities:
    urls: List[ParsedUrl] = field(default_factory=list)
    emails: List[str] = field(default_factory=list)  # e-mail domains
    upi: List[UpiLink] = field(default_factory=list)
    display_pairs: List[Tuple[str, str]] = field(default_factory=list)


def parse_url(raw: str) -> Optional[ParsedUrl]:
    raw = raw.strip().rstrip(_TRAIL)
    if not raw:
        return None
    has_scheme = re.match(r"^[a-z][a-z0-9+.\-]*://", raw, re.I) is not None
    try:
        parts = urlsplit(raw if has_scheme else "//" + raw)
        host = (parts.hostname or "").lower().rstrip(".")
    except ValueError:
        return None
    if not host:
        return None
    return ParsedUrl(
        raw=raw,
        scheme=parts.scheme.lower() if has_scheme else "",
        host=host,
        path=parts.path or "",
        query=parts.query or "",
        has_userinfo="@" in parts.netloc,
    )


def _looks_like_domain(host: str) -> bool:
    return bool(TLD(host).suffix)


def _find_urls(text: str) -> List[ParsedUrl]:
    found: List[ParsedUrl] = []
    seen = set()
    for m in _TOKEN_SPLIT.finditer(text):
        tok = m.group(0).strip().rstrip(_TRAIL)
        low = tok.lower()
        if not tok or "@" in tok and "://" not in tok:
            continue  # e-mail address, handled separately
        if low.startswith(("upi://", "tel:", "mailto:", "sms:")):
            continue
        if low.startswith(("http://", "https://", "ftp://", "www.")) or _BARE_DOMAIN.match(tok):
            pu = parse_url(tok)
            if pu and (pu.scheme or _looks_like_domain(pu.host)) and pu.raw not in seen:
                seen.add(pu.raw)
                found.append(pu)
    return found


def _parse_upi(raw: str) -> Optional[UpiLink]:
    try:
        qs = parse_qs(urlsplit(raw).query)
    except ValueError:
        return None
    first = lambda k: (qs.get(k) or [""])[0]
    return UpiLink(raw=raw, payee_vpa=first("pa"), payee_name=first("pn"), amount=first("am"), note=first("tn"))


def extract_entities(text: str) -> Entities:
    ent = Entities()
    ent.urls = _find_urls(text)

    for m in _EMAIL.finditer(text):
        dom = m.group(1).lower().rstrip(".")
        if dom not in ent.emails:
            ent.emails.append(dom)

    for m in re.finditer(r"upi://[^\s<>\"']+", text, re.I):
        link = _parse_upi(m.group(0))
        if link:
            ent.upi.append(link)

    for display, href in _HTML_LINK.findall(text):
        ent.display_pairs.append((re.sub(r"<[^>]+>", "", display), href))
    for display, href in _MD_LINK.findall(text):
        ent.display_pairs.append((display, href))
        pu = parse_url(href)
        if pu and all(u.raw != pu.raw for u in ent.urls):
            ent.urls.append(pu)
    for _, href in ent.display_pairs:
        pu = parse_url(href)
        if pu and all(u.raw != pu.raw for u in ent.urls):
            ent.urls.append(pu)
    return ent
