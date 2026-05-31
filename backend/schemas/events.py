"""Streaming event schema for the analysis orchestrator.

The orchestrator is an async generator of ``AnalysisEvent``s. The SSE endpoint
serializes each one; the blocking endpoint just waits for the terminal
``report`` event. A single event type with optional payload fields keeps the
frontend's discriminated-union handling simple.
"""

from typing import List, Literal, Optional

from pydantic import BaseModel

from schemas.analysis import (
    AnalysisPlan,
    BiasReport,
    ClaimAssessment,
    DimensionAssessment,
    ExtractedArticle,
    IssueMap,
    PlannedDimension,
)

AnalysisEventType = Literal[
    "ingested",            # article fetched/parsed
    "plan",                # planner finished
    "issue_map",           # debate map built (blind to the article)
    "dimensions_planned",  # the list of dimensions about to be evaluated
    "dimension_complete",  # one evaluator finished (streams in as they land)
    "claims_analyzed",     # claim analyst finished
    "synthesizing",        # fan-out done, synthesizer running
    "report",              # terminal: full BiasReport
    "error",               # terminal: something failed
]


class AnalysisEvent(BaseModel):
    type: AnalysisEventType
    message: Optional[str] = None

    article: Optional[ExtractedArticle] = None
    plan: Optional[AnalysisPlan] = None
    issue_map: Optional[IssueMap] = None
    dimensions: Optional[List[PlannedDimension]] = None
    assessment: Optional[DimensionAssessment] = None
    claims: Optional[List[ClaimAssessment]] = None
    report: Optional[BiasReport] = None


# --- v2 pipeline events (extract → ring0 ∥ ring1 → verdict) ---

from schemas.analysis import (  # noqa: E402
    ArgumentMap,
    ClaimCheck,
    CoherenceAssessment,
    FairnessReport,
    OmissionAssessment,
    RealityModel,
    RhetoricAssessment,
    StructuralAssessment,
    Verdict,
)

FairnessEventType = Literal[
    "ingested",
    "argument",      # ArgumentMap built
    "coherence",     # Ring 0 facets land independently
    "rhetoric",
    "structural",
    "reality",       # Ring 1 grounded map
    "claim_check",   # one spine claim checked (streams in as they land)
    "omission",
    "verdict",
    "report",        # terminal: full FairnessReport
    "error",
]


class FairnessEvent(BaseModel):
    type: FairnessEventType
    message: Optional[str] = None

    article: Optional[ExtractedArticle] = None
    argument: Optional[ArgumentMap] = None
    coherence: Optional[CoherenceAssessment] = None
    rhetoric: Optional[RhetoricAssessment] = None
    structural: Optional[StructuralAssessment] = None
    reality: Optional[RealityModel] = None
    claim_check: Optional[ClaimCheck] = None
    omission: Optional[OmissionAssessment] = None
    verdict: Optional[Verdict] = None
    report: Optional[FairnessReport] = None
