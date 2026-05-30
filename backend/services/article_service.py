"""Article ingestion service.

Owns turning a user request (a URL or pasted text) into a clean
``ExtractedArticle``. URL fetching uses httpx + BeautifulSoup to pull the main
body text; pasted text is normalized directly.
"""

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

    async def from_url(self, url: str) -> ExtractedArticle:
        logger.info(f"Fetching article from url={url}")
        try:
            async with httpx.AsyncClient(
                timeout=20.0, follow_redirects=True, headers={"User-Agent": _USER_AGENT}
            ) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                html = resp.text
        except httpx.HTTPError as e:
            logger.warning(f"Failed to fetch url={url}: {e}")
            raise ValueError(f"Could not fetch the URL: {e}") from e

        title, byline, body = self._extract_from_html(html)
        if not body.strip():
            raise ValueError("Could not extract readable article text from that URL.")

        return self._finalize(title=title or url, text=body, source_url=url, byline=byline)

    def from_text(self, text: str, title: Optional[str] = None) -> ExtractedArticle:
        if not text or not text.strip():
            raise ValueError("Article text is empty.")
        cleaned = self._normalize_whitespace(text)
        derived_title = title or self._derive_title(cleaned)
        return self._finalize(title=derived_title, text=cleaned, source_url=None, byline=None)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _extract_from_html(self, html: str):
        soup = BeautifulSoup(html, "html.parser")

        # Strip non-content elements.
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside", "form"]):
            tag.decompose()

        title = None
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = og_title["content"].strip()

        byline = None
        author_meta = soup.find("meta", attrs={"name": "author"})
        if author_meta and author_meta.get("content"):
            byline = author_meta["content"].strip()

        # Prefer paragraphs inside an <article>, else the densest container.
        container = soup.find("article") or soup.find("main") or soup.body or soup
        paragraphs = [p.get_text(" ", strip=True) for p in container.find_all("p")]
        paragraphs = [p for p in paragraphs if len(p) > 40]  # drop boilerplate snippets
        body = "\n\n".join(paragraphs)
        body = self._normalize_whitespace(body)
        return title, byline, body

    def _finalize(self, *, title: str, text: str, source_url, byline) -> ExtractedArticle:
        truncated = False
        if len(text) > self.max_chars:
            text = text[: self.max_chars]
            truncated = True
        word_count = len(text.split())
        return ExtractedArticle(
            title=title.strip()[:300],
            text=text,
            source_url=source_url,
            byline=byline,
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
