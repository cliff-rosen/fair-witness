"""Article ingestion service.

Owns turning a user request (a URL or pasted text) into a clean
``ExtractedArticle``. URL fetching uses httpx + BeautifulSoup to pull the main
body text; pasted text is normalized directly.
"""

import asyncio
import logging
import re
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from config.settings import settings
from schemas.analysis import ExtractedArticle

logger = logging.getLogger(__name__)

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36 FairWitness/0.1"
)


class ArticleService:
    """Owns ExtractedArticle creation from URL or raw text."""

    def __init__(self) -> None:
        self.max_chars = settings.MAX_ARTICLE_CHARS

    _MIN_BODY = 250  # below this we treat the page as blocked/stub and try the reader

    async def from_url(self, url: str) -> ExtractedArticle:
        logger.info(f"Fetching article from url={url}")

        # 1) Direct fetch — fast, and gives us rich og/JSON-LD metadata.
        html = await self._fetch_direct(url)
        if html:
            meta = self._extract_from_html(html)
            if self._usable(meta["body"]):
                return self._finalize(
                    title=meta["title"] or url,
                    text=meta["body"],
                    source_url=url,
                    byline=meta["byline"],
                    site_name=meta["site_name"] or self._domain(url),
                    published=meta["published"],
                )
            logger.info(f"Direct fetch unusable for {url}; trying reader fallback")

        # 2) Reader-service fallback (handles JS-heavy / Cloudflare / soft paywalls).
        reader = await self._fetch_via_reader(url)
        if reader and self._usable(reader["body"]):
            return self._finalize(
                title=reader["title"] or url,
                text=reader["body"],
                source_url=url,
                byline=None,
                site_name=self._domain(url),
                published=reader["published"],
            )

        # 3) Both failed — give an actionable message instead of a raw HTTP error.
        raise ValueError(
            "Couldn't read that page automatically. Some sites (e.g. archive.is, or "
            "paywalled / bot-protected pages) block readers. Try the original article's "
            "URL, or switch to “Paste text” and paste the article directly."
        )

    def from_text(self, text: str, title: Optional[str] = None) -> ExtractedArticle:
        if not text or not text.strip():
            raise ValueError("Article text is empty.")
        cleaned = self._normalize_whitespace(text)
        derived_title = title or self._derive_title(cleaned)
        return self._finalize(
            title=derived_title, text=cleaned, source_url=None, byline=None,
            site_name=None, published=None,
        )

    # ------------------------------------------------------------------
    # Fetching
    # ------------------------------------------------------------------

    async def _fetch_direct(self, url: str) -> Optional[str]:
        """Direct fetch with browser-like headers + one retry on soft blocks.
        Returns HTML, or None if blocked/errored (caller falls back to the reader)."""
        headers = {
            "User-Agent": _USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Upgrade-Insecure-Requests": "1",
        }
        try:
            async with httpx.AsyncClient(
                timeout=20.0, follow_redirects=True, headers=headers
            ) as client:
                resp = await client.get(url)
                if resp.status_code in (429, 403, 503):
                    await asyncio.sleep(1.5)  # one polite retry for soft limits
                    resp = await client.get(url)
                if resp.status_code >= 400:
                    logger.warning(f"Direct fetch {url} -> HTTP {resp.status_code}")
                    return None
                return resp.text
        except httpx.HTTPError as e:
            logger.warning(f"Direct fetch error for {url}: {e}")
            return None

    async def _fetch_via_reader(self, url: str) -> Optional[dict]:
        """Fallback through a reader service (Jina) that renders JS/Cloudflare
        pages server-side and returns clean text. Returns parsed dict or None."""
        base = settings.READER_FALLBACK_URL.strip()
        if not base:
            return None
        reader_url = base.rstrip("/") + "/" + url
        logger.info(f"Reader fallback for {url}")
        try:
            async with httpx.AsyncClient(
                timeout=40.0, follow_redirects=True,
                headers={"User-Agent": _USER_AGENT, "Accept": "text/plain"},
            ) as client:
                resp = await client.get(reader_url)
                if resp.status_code >= 400:
                    logger.warning(f"Reader fetch {url} -> HTTP {resp.status_code}")
                    return None
                return self._parse_reader(resp.text)
        except httpx.HTTPError as e:
            logger.warning(f"Reader fetch error for {url}: {e}")
            return None

    def _parse_reader(self, text: str) -> dict:
        """Parse Jina reader output (Title: / Published Time: / Markdown Content:)."""
        title = None
        published = None
        marker = re.search(r"(?im)^Markdown Content:\s*$", text)
        header = text[: marker.start()] if marker else text
        body = text[marker.end():] if marker else text
        for line in header.splitlines():
            low = line.lower()
            if low.startswith("title:") and not title:
                title = line.split(":", 1)[1].strip() or None
            elif low.startswith("published time:") and not published:
                published = line.split(":", 1)[1].strip() or None
        body = self._normalize_whitespace(self._strip_markdown(body))
        return {"title": title, "published": published, "body": body}

    # Phrases that mean we got an anti-bot / challenge / error page, not an article.
    _BLOCK_MARKERS = (
        "complete the captcha",
        "security check to access",
        "are you a human",
        "verify you are human",
        "please enable javascript",
        "just a moment",
        "attention required",
        "access denied",
        "checking your browser",
        "ddos protection",
        "captcha proves you are a human",
    )

    def _usable(self, body: str) -> bool:
        """Enough real text, and not an anti-bot/CAPTCHA page."""
        b = body.strip()
        if len(b) < self._MIN_BODY:
            return False
        low = b.lower()
        return not any(m in low for m in self._BLOCK_MARKERS)

    @staticmethod
    def _strip_markdown(md: str) -> str:
        md = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", md)          # images
        md = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", md)      # links -> link text
        out = [ln for ln in md.splitlines() if not re.match(r"^\s*https?://\S+\s*$", ln)]
        return "\n".join(out)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _extract_from_html(self, html: str) -> dict:
        soup = BeautifulSoup(html, "html.parser")

        # JSON-LD is the most reliable source for author/publisher/date — read it
        # BEFORE stripping <script> tags.
        ld = self._parse_json_ld(soup)

        def _meta(*, name=None, prop=None) -> Optional[str]:
            attrs = {"name": name} if name else {"property": prop}
            tag = soup.find("meta", attrs=attrs)
            v = tag.get("content").strip() if tag and tag.get("content") else None
            return v or None

        # Strip non-content elements before pulling body text.
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside", "form"]):
            tag.decompose()

        def _as_text(v):
            """Flatten JSON-LD/meta values (which may be lists/dicts) to a string."""
            if v is None:
                return None
            if isinstance(v, str):
                return v.strip() or None
            if isinstance(v, dict):
                return _as_text(v.get("name"))
            if isinstance(v, list):
                parts = [_as_text(x) for x in v]
                parts = [p for p in parts if p]
                return ", ".join(parts) or None
            return str(v)

        title = _meta(prop="og:title")
        if not title and soup.title and soup.title.string:
            title = soup.title.string.strip()

        site_name = _as_text(_meta(prop="og:site_name") or ld.get("site_name"))

        byline = _as_text(
            ld.get("author")
            or _meta(name="author")
            or _meta(name="byl")            # NYT
            or _meta(name="parsely-author")
            or _meta(prop="article:author")
        )
        # article:author is sometimes a URL — ignore those.
        if byline and byline.startswith("http"):
            byline = None

        published = _as_text(
            _meta(prop="article:published_time")
            or ld.get("published")
            or _meta(name="date")
            or _meta(name="pubdate")
            or _meta(name="article:published_time")
        )
        if not published:
            time_tag = soup.find("time")
            if time_tag:
                published = (time_tag.get("datetime") or time_tag.get_text(strip=True)) or None

        # Prefer paragraphs inside an <article>, else the densest container.
        container = soup.find("article") or soup.find("main") or soup.body or soup
        paragraphs = [p.get_text(" ", strip=True) for p in container.find_all("p")]
        paragraphs = [p for p in paragraphs if len(p) > 40]  # drop boilerplate snippets
        body = self._normalize_whitespace("\n\n".join(paragraphs))
        return {
            "title": title,
            "byline": byline,
            "site_name": site_name,
            "published": published,
            "body": body,
        }

    @staticmethod
    def _parse_json_ld(soup: BeautifulSoup) -> dict:
        """Best-effort author/publisher/date from schema.org JSON-LD blocks."""
        import json

        out: dict = {}

        def _name(v):
            if isinstance(v, dict):
                return v.get("name")
            if isinstance(v, list) and v:
                return _name(v[0])
            if isinstance(v, str):
                return v
            return None

        for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
            raw = tag.string or tag.get_text()
            if not raw:
                continue
            try:
                data = json.loads(raw)
            except Exception:
                continue
            candidates = data if isinstance(data, list) else [data]
            if isinstance(data, dict) and isinstance(data.get("@graph"), list):
                candidates = data["@graph"]
            for node in candidates:
                if not isinstance(node, dict):
                    continue
                if "author" not in out and node.get("author"):
                    out["author"] = _name(node.get("author"))
                if "published" not in out and node.get("datePublished"):
                    out["published"] = node.get("datePublished")
                if "site_name" not in out and node.get("publisher"):
                    out["site_name"] = _name(node.get("publisher"))
        return {k: v for k, v in out.items() if v}

    @staticmethod
    def _domain(url: str) -> Optional[str]:
        try:
            from urllib.parse import urlsplit

            host = urlsplit(url).netloc.lower()
            return host[4:] if host.startswith("www.") else host or None
        except Exception:
            return None

    def _finalize(
        self, *, title: str, text: str, source_url, byline, site_name=None, published=None
    ) -> ExtractedArticle:
        truncated = False
        if len(text) > self.max_chars:
            text = text[: self.max_chars]
            truncated = True
        word_count = len(text.split())
        return ExtractedArticle(
            title=title.strip()[:300],
            text=text,
            source_url=source_url,
            byline=(byline.strip()[:200] if byline else None),
            site_name=(site_name.strip()[:120] if site_name else None),
            published=(published.strip()[:60] if published else None),
            word_count=word_count,
            truncated=truncated,
        )

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @staticmethod
    def _derive_title(text: str) -> str:
        first_line = text.strip().splitlines()[0] if text.strip() else "Pasted article"
        if len(first_line) <= 120:
            return first_line
        return first_line[:117] + "..."
