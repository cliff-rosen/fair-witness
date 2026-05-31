"""Web search + fetch tools for the Ring 1 agent loop.

Ported and simplified from TableThat's tools/builtin/web.py — same Google
Programmable Search + httpx/BeautifulSoup fetch, minus the registry/db plumbing.
These are the tools the AgenticPromptCaller exposes to the model.
"""

import logging
from typing import Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from config.settings import settings

logger = logging.getLogger(__name__)

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
# Some sites (Wikipedia/Wikimedia) 403 fake browser UAs but welcome honest bots.
_BOT_HEADERS = {"User-Agent": "FairWitness/1.0 (article fairness research tool)"}
_BOT_DOMAINS = {"wikipedia.org", "wikimedia.org", "wiktionary.org", "wikidata.org"}


def _headers_for(url: str) -> dict:
    try:
        host = urlparse(url).hostname or ""
        if any(host == d or host.endswith("." + d) for d in _BOT_DOMAINS):
            return _BOT_HEADERS
    except Exception:
        pass
    return _BROWSER_HEADERS


# --- Tool definitions (Anthropic tool_use schemas) ---

SEARCH_WEB_TOOL = {
    "name": "search_web",
    "description": "Search the web. Returns titles, URLs, and snippets for matching results.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query"},
            "num_results": {"type": "integer", "description": "1-10, default 5"},
        },
        "required": ["query"],
    },
}

FETCH_WEBPAGE_TOOL = {
    "name": "fetch_webpage",
    "description": "Fetch a webpage and extract its text content. Use to read a specific URL and verify details.",
    "input_schema": {
        "type": "object",
        "properties": {"url": {"type": "string", "description": "URL to fetch"}},
        "required": ["url"],
    },
}


async def execute_search_web(params: dict[str, Any]) -> tuple[str, list[str]]:
    """Google Programmable Search. Returns (rendered_text, result_urls)."""
    query = (params.get("query") or "").strip()
    if not query:
        return "Error: search query is required.", []
    num = min(max(int(params.get("num_results", 5) or 5), 1), 10)
    if not settings.GOOGLE_SEARCH_API_KEY or not settings.GOOGLE_SEARCH_ENGINE_ID:
        return "Error: web search is not configured.", []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://www.googleapis.com/customsearch/v1",
                params={
                    "key": settings.GOOGLE_SEARCH_API_KEY,
                    "cx": settings.GOOGLE_SEARCH_ENGINE_ID,
                    "q": query,
                    "num": num,
                },
            )
            resp.raise_for_status()
        items = resp.json().get("items", [])
    except httpx.HTTPError as e:
        logger.warning(f"search_web failed: {e}")
        return f"Error: web search failed — {e}", []

    if not items:
        return f"No results found for: {query}", []
    lines = [f"Search results for: {query}\n"]
    urls: list[str] = []
    for i, it in enumerate(items[:num], 1):
        url = it.get("link", "")
        urls.append(url)
        lines += [f"{i}. {it.get('title','')}", f"   URL: {url}", f"   {it.get('snippet','')}", ""]
    return "\n".join(lines), urls


async def execute_fetch_webpage(params: dict[str, Any], max_chars: int = 8000) -> str:
    """Fetch + extract readable text from a URL."""
    url = (params.get("url") or "").strip()
    if not url:
        return "Error: URL is required."
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=_headers_for(url)) as client:
            resp = await client.get(url)
            resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "html.parser")
        title = soup.find("title")
        title = title.get_text(strip=True) if title else ""
        for tag in soup(["script", "style", "nav", "footer", "aside", "header", "noscript", "svg", "iframe"]):
            tag.decompose()
        text = "\n".join(ln.strip() for ln in soup.get_text("\n").splitlines() if ln.strip())
        if len(text) > max_chars:
            text = text[:max_chars] + " …(truncated)"
        return f"URL: {url}\nTitle: {title}\n\n{text}"
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} fetching {url}"
    except httpx.HTTPError as e:
        return f"Error: failed to fetch {url} — {e}"
