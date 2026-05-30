"""Analysis orchestrator service (V2).

The pipeline:

    Planner
       │  (names the topic, classifies, extracts claims, selects dimensions)
       ▼
    Issue Map  ── built BLIND to the article, from the topic alone
       │
       ▼
    Fan-out (concurrent):
       • dimension specialists  — HOW the article says it (map-aware)
       • claim analyst          — WHAT it says, claims diffed against the map
       │
       ▼
    Synthesizer  ── two-axis verdict (presentation + substantive)

Exposed as an async generator of typed ``AnalysisEvent``s so the UI can render
the pipeline live. A blocking ``analyze`` helper drains the same generator.
"""

import asyncio
import logging
from typing import AsyncGenerator, List, Union

from agents.claim_analyst import ClaimAnalystPromptCaller
from agents.dimension_evaluator import DimensionEvaluatorPromptCaller
from agents.issue_map_builder import IssueMapBuilderPromptCaller, brief_issue_map
from agents.planner import PlannerPromptCaller
from agents.synthesizer import SynthesizerPromptCaller
from config.settings import settings
from schemas.analysis import (
    BiasReport,
    ClaimAnalysis,
    DimensionAssessment,
    ExtractedArticle,
)
from schemas.events import AnalysisEvent

logger = logging.getLogger(__name__)


class AnalysisService:
    """Owns the planner -> issue-map -> fan-out -> synthesize orchestration."""

    def __init__(self) -> None:
        self.planner = PlannerPromptCaller()
        self.map_builder = IssueMapBuilderPromptCaller()
        self.claim_analyst = ClaimAnalystPromptCaller()
        self.synthesizer = SynthesizerPromptCaller()
        self._semaphore = asyncio.Semaphore(settings.MAX_PARALLEL_EVALUATORS)

    async def analyze_stream(
        self, article: ExtractedArticle
    ) -> AsyncGenerator[AnalysisEvent, None]:
        """Run the pipeline, yielding events as each stage progresses."""
        try:
            yield AnalysisEvent(type="ingested", article=article)

            # --- Stage 1: Planner ---
            logger.info(f"Planning analysis for article '{article.title[:60]}'")
            plan = await self.planner.plan(article.title, article.text)
            yield AnalysisEvent(type="plan", plan=plan)

            # --- Stage 2: Issue Map (blind to the article) ---
            logger.info(f"Building issue map for topic '{plan.topic[:60]}'")
            issue_map = await self.map_builder.build(plan.topic, plan.main_subject)
            yield AnalysisEvent(type="issue_map", issue_map=issue_map)
            map_reference = brief_issue_map(issue_map)

            yield AnalysisEvent(type="dimensions_planned", dimensions=plan.dimensions)

            # --- Stage 3+4: Fan-out — dimension specialists + claim analyst ---
            logger.info(
                f"Fanning out {len(plan.dimensions)} dimension evaluators + claim analyst"
            )

            async def run_dimension(planned) -> DimensionAssessment:
                async with self._semaphore:
                    evaluator = DimensionEvaluatorPromptCaller(planned)
                    return await evaluator.evaluate(article.title, article.text, map_reference)

            async def run_claims() -> ClaimAnalysis:
                async with self._semaphore:
                    return await self.claim_analyst.analyze(
                        article.title, article.text, plan, issue_map
                    )

            tasks: List[asyncio.Task] = [
                asyncio.create_task(run_dimension(p)) for p in plan.dimensions
            ]
            tasks.append(asyncio.create_task(run_claims()))

            assessments: List[DimensionAssessment] = []
            claims: List = []
            for coro in asyncio.as_completed(tasks):
                result: Union[DimensionAssessment, ClaimAnalysis] = await coro
                if isinstance(result, ClaimAnalysis):
                    claims = result.claims
                    yield AnalysisEvent(type="claims_analyzed", claims=claims)
                else:
                    assessments.append(result)
                    yield AnalysisEvent(type="dimension_complete", assessment=result)

            # Stable, plan-ordered list for the synthesizer + report.
            order = {p.key: i for i, p in enumerate(plan.dimensions)}
            assessments.sort(key=lambda a: order.get(a.key, 999))

            # --- Stage 5: Synthesize ---
            yield AnalysisEvent(type="synthesizing")
            logger.info("Synthesizing two-axis verdict")
            overall = await self.synthesizer.synthesize(plan, issue_map, assessments, claims)

            report = BiasReport(
                article=article,
                plan=plan,
                issue_map=issue_map,
                dimensions=assessments,
                claims=claims,
                overall=overall,
            )
            logger.info(
                f"Analysis complete: overall={overall.overall_score} "
                f"(presentation={overall.presentation_score}, "
                f"substantive={overall.substantive_score}) label='{overall.fairness_label}'"
            )
            yield AnalysisEvent(type="report", report=report)

        except Exception as e:
            logger.error(f"Analysis pipeline failed: {e}", exc_info=True)
            yield AnalysisEvent(type="error", message=str(e))

    async def analyze(self, article: ExtractedArticle) -> BiasReport:
        """Blocking variant: drain the stream and return the final report."""
        async for event in self.analyze_stream(article):
            if event.type == "report" and event.report is not None:
                return event.report
            if event.type == "error":
                raise RuntimeError(event.message or "Analysis failed")
        raise RuntimeError("Analysis ended without producing a report")
