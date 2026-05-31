"""v2 orchestrator — the two-ring pipeline.

    Ingest → Extract(ArgumentMap)
           → fan out:  Ring 0 (coherence ∥ rhetoric ∥ structural, text-only)
                       Ring 1 (reality ∥ claim-checks over the spine, web-grounded)
           → Omission (diff vs reality)
           → Synthesize (two-axis Verdict)
           → FairnessReport

Async generator of FairnessEvents so the UI can render each piece live; a
blocking `analyze` drains it. Replaces AnalysisService at cutover.
"""

import asyncio
import logging
from typing import AsyncGenerator, List, Optional

from agents.extractor import ExtractorPromptCaller
from agents.ring0_coherence import CoherencePromptCaller
from agents.ring0_rhetoric import RhetoricPromptCaller
from agents.ring0_structural import StructuralPromptCaller
from agents.ring1_claimcheck import ClaimCheckAgent
from agents.ring1_omission import OmissionAgent
from agents.ring1_reality import RealityModelAgent
from agents.synthesizer_v2 import SynthesizerV2PromptCaller
from schemas.analysis import (
    ClaimCheck,
    ExtractedArticle,
    FairnessReport,
    Ring0Result,
    Ring1Result,
)
from schemas.events import FairnessEvent
from services import report_repository

logger = logging.getLogger(__name__)

_SPINE_SIZE = 5        # reality-check only the top-N load-bearing claims (bounds cost)
_WEB_CONCURRENCY = 4   # max concurrent agentic (web) loops


class FairnessService:
    def __init__(self) -> None:
        self.extractor = ExtractorPromptCaller()
        self.coherence = CoherencePromptCaller()
        self.rhetoric = RhetoricPromptCaller()
        self.structural = StructuralPromptCaller()
        self.reality_agent = RealityModelAgent()
        self.claim_agent = ClaimCheckAgent()
        self.omission_agent = OmissionAgent()
        self.synth = SynthesizerV2PromptCaller()

    async def analyze_stream(
        self,
        article: ExtractedArticle,
        content_hash: Optional[str] = None,
        source_url: Optional[str] = None,
    ) -> AsyncGenerator[FairnessEvent, None]:
        try:
            yield FairnessEvent(type="ingested", article=article)

            # --- EXTRACT: the argument map (the substrate for both rings) ---
            am = await self.extractor.extract(article.title, article.text)
            yield FairnessEvent(type="argument", argument=am)

            spine = sorted(am.claims, key=lambda c: -c.load_bearing)[:_SPINE_SIZE]
            sem = asyncio.Semaphore(_WEB_CONCURRENCY)

            async def r0(name, coro):
                return name, await coro

            async def web(name, coro):
                async with sem:
                    return name, await coro

            tasks: List[asyncio.Task] = [
                asyncio.create_task(r0("coherence", self.coherence.analyze(article.title, article.text, am))),
                asyncio.create_task(r0("rhetoric", self.rhetoric.analyze(article.title, article.text, am))),
                asyncio.create_task(r0("structural", self.structural.analyze(article.title, article.text, am))),
                asyncio.create_task(web("reality", self.reality_agent.build(am.topic, am.main_subject))),
            ]
            for c in spine:
                tasks.append(asyncio.create_task(web("claim", self.claim_agent.check(c, am.topic))))

            r0_out: dict = {}
            reality = None
            claim_checks: List[ClaimCheck] = []
            for fut in asyncio.as_completed(tasks):
                name, val = await fut
                if name == "claim":
                    self._strip_self_citation(val, source_url)
                    claim_checks.append(val)
                    yield FairnessEvent(type="claim_check", claim_check=val)
                elif name == "reality":
                    reality = val
                    yield FairnessEvent(type="reality", reality=val)
                else:
                    r0_out[name] = val
                    yield FairnessEvent(type=name, **{name: val})

            # Stable spine ordering for the report.
            order = {c.id: i for i, c in enumerate(spine)}
            claim_checks.sort(key=lambda c: order.get(c.claim_id, 999))

            # --- Ring 1: omission (diff article vs grounded reality) ---
            omission = await self.omission_agent.analyze(
                article.title, article.text, am, reality, claim_checks
            )
            yield FairnessEvent(type="omission", omission=omission)

            # --- Synthesize: two-axis verdict ---
            verdict = await self.synth.synthesize(
                am, r0_out["coherence"], r0_out["rhetoric"], r0_out["structural"],
                reality, claim_checks, omission,
            )
            yield FairnessEvent(type="verdict", verdict=verdict)

            report = FairnessReport(
                article=article,
                argument=am,
                ring0=Ring0Result(
                    coherence=r0_out["coherence"], rhetoric=r0_out["rhetoric"], structural=r0_out["structural"]
                ),
                ring1=Ring1Result(reality=reality, claim_checks=claim_checks, omission=omission),
                verdict=verdict,
            )
            logger.info(
                f"v2 analysis complete: coherence={verdict.coherence_score} "
                f"correspondence={verdict.correspondence_score} overall={verdict.overall_score}"
            )

            # Persist for sharing + Recent (best-effort; stamps report_id/created_at).
            if report_repository.is_enabled() and content_hash:
                try:
                    await report_repository.save_report(report, content_hash, source_url)
                    logger.info(f"Stored shareable report {report.report_id}")
                except Exception as e:
                    logger.error(f"Failed to store report: {e}", exc_info=True)

            yield FairnessEvent(type="report", report=report)

        except Exception as e:
            logger.error(f"v2 pipeline failed: {e}", exc_info=True)
            yield FairnessEvent(type="error", message=str(e))

    @staticmethod
    def _strip_self_citation(cc: ClaimCheck, source_url: Optional[str]) -> None:
        """Don't let the article being analyzed corroborate its own claims."""
        if not source_url:
            return
        cc.evidence = [e for e in cc.evidence if e.source_url != source_url]
        cc.sources = [s for s in cc.sources if s != source_url]

    async def analyze(
        self,
        article: ExtractedArticle,
        content_hash: Optional[str] = None,
        source_url: Optional[str] = None,
    ) -> FairnessReport:
        async for ev in self.analyze_stream(article, content_hash, source_url):
            if ev.type == "report" and ev.report is not None:
                return ev.report
            if ev.type == "error":
                raise RuntimeError(ev.message or "Analysis failed")
        raise RuntimeError("Analysis ended without producing a report")
