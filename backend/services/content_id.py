"""Stable content id for dedup ("has this article already been analyzed?").

For a URL we hash the *normalized* URL (lowercased host, no `www.`, no fragment,
tracking params like `utm_*` / `fbclid` stripped — important since links get
shared from Facebook). For pasted text we hash the whitespace-normalized text.
The same function is used at precheck time and at save time so they agree.
"""

import hashlib
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_TRACKING_PARAMS = {
    "fbclid", "gclid", "gbraid", "wbraid", "msclkid", "mc_cid", "mc_eid",
    "igshid", "ref", "ref_src", "ref_url", "_ga",
}


def normalize_url(url: str) -> str:
    p = urlsplit(url.strip())
    scheme = (p.scheme or "https").lower()
    netloc = p.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = p.path.rstrip("/")
    # Keep meaningful query params (some sites use ?id=...), drop tracking junk.
    kept = [
        (k, v)
        for k, v in parse_qsl(p.query, keep_blank_values=False)
        if k.lower() not in _TRACKING_PARAMS and not k.lower().startswith("utm_")
    ]
    kept.sort()
    return urlunsplit((scheme, netloc, path, urlencode(kept), ""))


def compute_content_hash(url: str | None = None, text: str | None = None) -> str:
    if url and url.strip():
        basis = "url:" + normalize_url(url)
    else:
        basis = "text:" + re.sub(r"\s+", " ", (text or "").strip().lower())
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()
