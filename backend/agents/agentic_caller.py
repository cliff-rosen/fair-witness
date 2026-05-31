"""Agentic prompt caller — an LLM with web tools in a loop.

This is the Ring 1 counterpart to BasePromptCaller. Where BasePromptCaller does
a single forced-output call (no tools, no loop), this exposes web search + fetch
and loops — the model gathers evidence over several turns, then is required to
call `emit_result` with arguments matching its Pydantic schema.

Generalizes TableThat's `_research_web_core`: same Anthropic tool loop (force a
search first, execute tool calls, feed results back), but the terminal tool is a
typed `emit_result` instead of `submit_answer`. Returns the validated model plus
the list of source URLs it touched (for citations).
"""

import logging
import re
from typing import Optional, Tuple, Type

from pydantic import BaseModel

from agents.base_prompt_caller import _TOOL_NAME, _inline_refs, get_shared_client
from agents.web_tools import (
    FETCH_WEBPAGE_TOOL,
    SEARCH_WEB_TOOL,
    execute_fetch_webpage,
    execute_search_web,
)
from config.settings import settings
from schemas.analysis import WebStep

logger = logging.getLogger(__name__)


class AgenticPromptCaller:
    """LLM + web tools in a loop, ending in a forced structured output."""

    def __init__(
        self,
        response_model: Type[BaseModel],
        system_message: str,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 3072,
        max_steps: Optional[int] = None,
        force_search_first: bool = True,
    ):
        self.response_model = response_model
        self.system_message = system_message
        self.model = model or settings.WEB_MODEL
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_steps = max_steps or settings.WEB_MAX_STEPS
        self.force_search_first = force_search_first
        self.client = get_shared_client()

    def _emit_tool(self) -> dict:
        return {
            "name": _TOOL_NAME,
            "description": (
                f"Return the final {self.response_model.__name__}. Call this exactly once, "
                "AFTER you have gathered enough evidence via search/fetch. Provide arrays as "
                "native JSON arrays, never strings."
            ),
            "input_schema": _inline_refs(self.response_model.model_json_schema()),
        }

    async def invoke(self, user_content: str) -> Tuple[BaseModel, list[str], list[WebStep], dict]:
        """Run the tool loop; return (validated_result, source_urls, trace, corpus).

        `corpus` = {"by_url": {url: page_text}, "all": "<all retrieved text>"} —
        the text actually retrieved, used to verify cited quotes against."""
        tools = [SEARCH_WEB_TOOL, FETCH_WEBPAGE_TOOL, self._emit_tool()]
        messages: list[dict] = [{"role": "user", "content": user_content}]
        sources: list[str] = []
        trace: list[WebStep] = []
        pages: dict[str, str] = {}      # fetched url -> page text
        blob: list[str] = []            # all retrieved text (snippets + pages)

        for step in range(self.max_steps):
            kwargs = dict(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=self.system_message,
                tools=tools,
                messages=messages,
            )
            if step == 0 and self.force_search_first:
                kwargs["tool_choice"] = {"type": "tool", "name": "search_web"}
            else:
                kwargs["tool_choice"] = {"type": "auto"}

            resp = await self.client.messages.create(**kwargs)
            tool_uses = [b for b in resp.content if getattr(b, "type", None) == "tool_use"]

            emit = next((t for t in tool_uses if t.name == _TOOL_NAME), None)
            if emit is not None:
                return (self.response_model.model_validate(emit.input), _dedup(sources), trace,
                        {"by_url": pages, "all": "\n".join(blob)})

            if not tool_uses:
                # Model answered in prose — nudge it to emit the structured result.
                messages.append({"role": "assistant", "content": resp.content})
                messages.append({"role": "user", "content": "Now call emit_result with your final result."})
                continue

            messages.append({"role": "assistant", "content": resp.content})
            results = []
            for tu in tool_uses:
                if tu.name == "search_web":
                    text, urls = await execute_search_web(tu.input)
                    sources.extend(urls)
                    blob.append(text)
                    trace.append(WebStep(kind="search", query=(tu.input.get("query") or "").strip() or None,
                                         result_count=len(urls)))
                elif tu.name == "fetch_webpage":
                    text = await execute_fetch_webpage(tu.input)
                    url = (tu.input.get("url") or "").strip()
                    if url:
                        sources.append(url)
                        pages[url] = text
                    blob.append(text)
                    trace.append(WebStep(kind="fetch", url=url or None, title=_title_of(text)))
                else:
                    text = f"Unknown tool: {tu.name}"
                results.append({"type": "tool_result", "tool_use_id": tu.id, "content": text})
            messages.append({"role": "user", "content": results})

        # Step cap reached — force the structured result from what was gathered.
        logger.info(f"{self.response_model.__name__}: step cap hit, forcing emit_result")
        messages.append({
            "role": "user",
            "content": "Stop searching. Call emit_result now using only what you've already found.",
        })
        resp = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=self.system_message,
            tools=[self._emit_tool()],
            tool_choice={"type": "tool", "name": _TOOL_NAME},
            messages=messages,
        )
        emit = next((b for b in resp.content if getattr(b, "type", None) == "tool_use"), None)
        if emit is None:
            raise RuntimeError(f"{self.response_model.__name__}: no structured result after step cap")
        return (self.response_model.model_validate(emit.input), _dedup(sources), trace,
                {"by_url": pages, "all": "\n".join(blob)})


def _dedup(urls: list[str]) -> list[str]:
    seen, out = set(), []
    for u in urls:
        if u and u not in seen:
            seen.add(u)
            out.append(u)
    return out


def _title_of(fetch_text: str) -> Optional[str]:
    """Pull the 'Title:' line out of a fetch_webpage result, if present."""
    for line in fetch_text.splitlines():
        if line.startswith("Title:"):
            t = line[len("Title:"):].strip()
            return t or None
    return None


def _norm(s: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace — for tolerant matching."""
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", (s or "").lower())).strip()


def verify_evidence(items, corpus: dict) -> None:
    """Set `verified` on each Evidence by checking the quote actually appears in
    the text we retrieved. A quote is verified against its cited page if we
    fetched it, else against the whole retrieved corpus. Quotes too short to be
    meaningful, or absent from everything retrieved, are marked unverified.

    This is the anti-hallucination gate: a fabricated quote can never be marked
    verified, because it isn't in anything we actually pulled."""
    by_url = {u: _norm(t) for u, t in corpus.get("by_url", {}).items()}
    all_text = _norm(corpus.get("all", ""))
    for ev in items or []:
        q = _norm(ev.quote)
        if len(q) < 12:  # too short to verify meaningfully
            ev.verified = False
            continue
        page = by_url.get(ev.source_url)
        ev.verified = (q in page) if page is not None else (q in all_text)
