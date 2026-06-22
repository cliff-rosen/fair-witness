"""Streaming event schema for the analysis orchestrator (v2 two-ring pipeline).

The orchestrator is an async generator of ``FairnessEvent``s. The SSE endpoint
serializes each one; the blocking endpoint just waits for the terminal
``report`` event. A single event type with optional payload fields keeps the
frontend's discriminated-union handling simple.
"""

from typing import Literal, Optional

from pydantic import BaseModel

from schemas.analysis import (
    ArgumentMap,
    ClaimCheck,
    CoherenceAssessment,
    ExtractedArticle,
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
