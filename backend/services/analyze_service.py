"""The analyze orchestrator, with complete diagnostics.

    Extract claims → Topic map (blind, web) → Place claims on map → Verdict

Deliberately simple and linear (no fan-out) so the whole run is easy to follow.
Every stage is wrapped by the Recorder, which captures the stage's full input,
its system prompt + rendered user message, and its full output — so the
diagnostics screen can show the entire pipeline with nothing hidden.
"""

import logging
import time
from typing import Any, Awaitable, Callable, Optional, Tuple

from agents.analyze_extractor import ClaimExtractor
from agents.analyze_placer import ClaimPlacer
from agents.analyze_synth import Synthesizer
from agents.analyze_topic_mapper import TopicMapper
from schemas.analysis import ExtractedArticle
from schemas.analyze import (
    AnalyzeReport,
    AnalyzeResult,
    ClaimSet,
    PipelineDiagnostics,
    StageRecord,
    TopicMap,
    Verdict,
)

logger = logging.getLogger(__name__)


def _jsonable(value: Any) -> Any:
    """Best-effort convert pydantic models / nested structures to plain JSON."""
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    return value


class Recorder:
    """Accumulates a StageRecord per stage. Capture is total by construction:
    every stage goes through `run`, which stores both its input and its output."""

    def __init__(self) -> None:
        self.stages: list[StageRecord] = []

    async def run(
        self,
        name: str,
        title: str,
        kind: str,
        logical_input: Any,
        call: Callable[[], Awaitable[Tuple[Any, dict]]],
    ) -> Any:
        """Run a stage `call` that returns (result, io); record everything."""
        t0 = time.monotonic()
        try:
            result, io = await call()
        except Exception as e:
            self.stages.append(
                StageRecord(
                    name=name, title=title, kind=kind, ok=False, error=str(e),
                    input=_jsonable(logical_input),
                    duration_ms=int((time.monotonic() - t0) * 1000),
                )
            )
            raise
        self.stages.append(
            StageRecord(
                name=name,
                title=title,
                kind=kind,
                model=io.get("model"),
                system_prompt=io.get("system_prompt"),
                user_message=io.get("user_message"),
                input=_jsonable(logical_input),
                output=_jsonable(result),
                sources=io.get("sources", []) or [],
                web_steps=io.get("web_steps"),
                duration_ms=int((time.monotonic() - t0) * 1000),
            )
        )
        return result

    def record_code(self, name: str, title: str, logical_input: Any, output: Any, ms: int = 0) -> None:
        """Record a pure-code step (no LLM)."""
        self.stages.append(
            StageRecord(
                name=name, title=title, kind="code",
                input=_jsonable(logical_input), output=_jsonable(output), duration_ms=ms,
            )
        )


class AnalyzeService:
    """extract → map → place → verdict, with full per-stage diagnostics."""

    def __init__(self) -> None:
        self.extractor = ClaimExtractor()
        self.mapper = TopicMapper()
        self.placer = ClaimPlacer()
        self.synth = Synthesizer()

    async def analyze(self, article: ExtractedArticle) -> AnalyzeResult:
        rec = Recorder()
        t0 = time.monotonic()

        # Stage 1 — extract the claims (article only).
        claims: ClaimSet = await rec.run(
            "extract", "1 · Extract claims", "structured",
            {"title": article.title, "text": article.text},
            lambda: self.extractor.extract(article.title, article.text),
        )

        # Stage 2 — map the topic (blind to the article, web-grounded).
        topic_map: TopicMap = await rec.run(
            "topic_map", "2 · Map the topic (blind)", "agentic",
            {"topic": claims.topic, "main_subject": claims.main_subject},
            lambda: self.mapper.build(claims.topic, claims.main_subject),
        )

        # Stage 3 — place each claim on the map.
        placements = await rec.run(
            "place", "3 · Place claims on the map", "structured",
            {"claims": claims, "topic_map": topic_map},
            lambda: self.placer.place(claims, topic_map),
        )

        # Stage 4 — synthesize the two-axis verdict.
        verdict: Verdict = await rec.run(
            "verdict", "4 · Verdict", "structured",
            {"claims": claims, "topic_map": topic_map, "placements": placements},
            lambda: self.synth.synthesize(claims, topic_map, placements),
        )

        report = AnalyzeReport(
            article=article,
            claims=claims,
            topic_map=topic_map,
            placements=placements,
            verdict=verdict,
        )
        diagnostics = PipelineDiagnostics(
            article_title=article.title,
            stages=rec.stages,
            total_ms=int((time.monotonic() - t0) * 1000),
        )
        logger.info(
            f"analyze complete: overall={verdict.overall_score} "
            f"(substantive={verdict.substantive_score}, presentation={verdict.presentation_score})"
        )
        return AnalyzeResult(report=report, diagnostics=diagnostics)
