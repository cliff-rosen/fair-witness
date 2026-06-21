"""Schemas for the "best of both" (v3) pipeline + its diagnostics.

The v3 pipeline merges the two strengths we identified across v1 and v2:

  1. EXTRACT   — pull the article's load-bearing claims (precise claim list).
  2. TOPIC MAP — build, BLIND to the article, a cited map of the debate:
                 the sides, each side's talking points flagged by substantiation,
                 and the settled facts. (v1's discourse map + v2's grounding.)
  3. PLACE     — snap each claim onto the map: where it sits (settled fact /
                 contradicts / a side's talking point / novel) AND how the
                 article handles it, with a source receipt where one applies.
  4. VERDICT   — roll the placements up into a two-axis fairness call.

Every stage's full input and output is captured in PipelineDiagnostics so the
diagnostics screen can show the whole pipeline, nothing hidden.

Scoring convention: integers 0-100, where 100 = perfectly fair. Higher = better.
"""

from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from schemas.analysis import ExtractedArticle, _coerce_json_list

# ---------------------------------------------------------------------------
# Shared vocab
# ---------------------------------------------------------------------------

AsPresented = Literal["asserted", "attributed", "hedged"]

IssueStructure = Literal[
    "settled",
    "genuinely-two-sided",
    "multi-sided",
    "not-adversarial",
]

Substantiation = Literal[
    "substantiated",
    "partly-substantiated",
    "contested",
    "unsubstantiated",
]

# Where an article claim sits relative to the independent topic map (v1's idea).
ClaimLocation = Literal[
    "matches_settled_fact",
    "contradicts_settled_fact",
    "substantiated_argument",
    "unsubstantiated_talking_point",
    "novel_or_unverifiable",
]

# How the article handles that claim, given where it sits.
ClaimHandling = Literal[
    "fair",
    "overstated",
    "asserted_as_fact",   # contested point stated flatly in the author's voice
    "missing_context",
    "misleading",
]

FairnessLabel = Literal[
    "Highly Fair",
    "Mostly Fair",
    "Mixed",
    "Slanted",
    "Heavily Biased",
]


# ---------------------------------------------------------------------------
# Stage 1 — Extract claims
# ---------------------------------------------------------------------------

class Claim(BaseModel):
    """One load-bearing claim the article makes."""

    id: str = Field(description="Short stable id, e.g. 'c1'.")
    text: str = Field(description="The claim as a tight paraphrase or short quote.")
    as_presented: AsPresented = Field(
        description="asserted (author's voice) / attributed (to a source) / hedged."
    )
    centrality: int = Field(
        ge=0, le=100, description="How load-bearing to the thesis (100 = essential)."
    )


class ClaimSet(BaseModel):
    """What the article is and the claims it rests on (looks only at the article)."""

    genre: str = Field(description="news report, op-ed, analysis, feature, blog, …")
    topic: str
    main_subject: str = Field(description="The central person/org/event covered.")
    summary: str = Field(description="2–3 sentence neutral summary.")
    thesis: str = Field(description="The central point the piece advances.")
    claims: List[Claim] = Field(default_factory=list)

    @field_validator("claims", mode="before")
    @classmethod
    def _coerce(cls, v: Any) -> Any:
        return _coerce_json_list(v)


# ---------------------------------------------------------------------------
# Stage 2 — Topic map (blind to the article, web-grounded)
# ---------------------------------------------------------------------------

class TalkingPoint(BaseModel):
    point: str = Field(description="A point a side typically makes.")
    substantiation: Substantiation = Field(description="How well it actually holds up.")


class Side(BaseModel):
    name: str = Field(description="Short label for the position.")
    position: str = Field(description="One sentence: what this side holds.")
    talking_points: List[TalkingPoint] = Field(default_factory=list)

    @field_validator("talking_points", mode="before")
    @classmethod
    def _coerce(cls, v: Any) -> Any:
        return _coerce_json_list(v)


class SettledFact(BaseModel):
    fact: str
    source_url: Optional[str] = Field(default=None, description="A source, where found.")
    confidence: int = Field(ge=0, le=100, description="How settled (100 = beyond dispute).")


class TopicMap(BaseModel):
    """An independent, cited map of the debate — the yardstick for the claims."""

    topic: str
    structure: IssueStructure = Field(description="How the topic is actually structured.")
    structure_note: str = Field(
        description="Explain the structure; flag if it's wrongly framed as two-sided."
    )
    sides: List[Side] = Field(default_factory=list)
    settled_facts: List[SettledFact] = Field(default_factory=list)
    common_biases: List[str] = Field(
        default_factory=list, description="How coverage of this topic typically skews."
    )
    sources: List[str] = Field(default_factory=list, description="URLs consulted.")

    @field_validator("sides", "settled_facts", "common_biases", mode="before")
    @classmethod
    def _coerce(cls, v: Any) -> Any:
        return _coerce_json_list(v)


# ---------------------------------------------------------------------------
# Stage 3 — Place each claim on the map
# ---------------------------------------------------------------------------

class ClaimPlacement(BaseModel):
    """One article claim, located on the topic map and judged for handling."""

    claim_id: str = Field(default="", description="Echoes the Claim id (set by code).")
    claim: str = Field(default="", description="The claim text (set by code).")
    location: ClaimLocation = Field(description="Where the claim sits on the map.")
    side: str = Field(default="", description="Which side it belongs to, if any.")
    handling: ClaimHandling = Field(description="How the article handles it.")
    note: str = Field(description="One or two sentences explaining the call.")
    source_quote: str = Field(default="", description="A supporting quote from the map, if any.")
    source_url: str = Field(default="", description="Where that quote/fact came from, if any.")


class PlacementSet(BaseModel):
    """Wrapper so the placer can emit a list under forced tool-use."""

    placements: List[ClaimPlacement] = Field(default_factory=list)

    @field_validator("placements", mode="before")
    @classmethod
    def _coerce(cls, v: Any) -> Any:
        return _coerce_json_list(v)


# ---------------------------------------------------------------------------
# Stage 4 — Verdict
# ---------------------------------------------------------------------------

class Verdict(BaseModel):
    """Two-axis fairness call: substantive (vs the map) + presentation (manner)."""

    substantive_score: int = Field(
        ge=0, le=100, description="Does it track the map? (cherry-picking/contradiction/laundering lower it)"
    )
    presentation_score: int = Field(
        ge=0, le=100, description="How it's written — loaded language, framing."
    )
    overall_score: int = Field(ge=0, le=100, description="Reasoned blend, NOT an average.")
    fairness_label: FairnessLabel
    both_sidesing: bool = Field(
        default=False, description="Treats a settled question as a live two-sided debate."
    )
    false_consensus: bool = Field(
        default=False, description="Presents a genuinely contested point as settled."
    )
    summary: str = Field(description="Plain-language verdict for a reader.")
    strengths: List[str] = Field(default_factory=list)
    concerns: List[str] = Field(default_factory=list)

    @field_validator("strengths", "concerns", mode="before")
    @classmethod
    def _coerce(cls, v: Any) -> Any:
        return _coerce_json_list(v)


# ---------------------------------------------------------------------------
# Assembled report
# ---------------------------------------------------------------------------

class BoeReport(BaseModel):
    """The complete v3 report: extract → map → place → verdict."""

    article: ExtractedArticle
    claims: ClaimSet
    topic_map: TopicMap
    placements: List[ClaimPlacement] = Field(default_factory=list)
    verdict: Verdict
    report_id: Optional[str] = None
    created_at: Optional[str] = None


# ---------------------------------------------------------------------------
# Diagnostics — captures every stage, completely
# ---------------------------------------------------------------------------

StageKind = Literal["code", "structured", "agentic"]


class StageRecord(BaseModel):
    """One pipeline stage, captured whole: its inputs and its output."""

    name: str = Field(description="Stable id, e.g. 'extract'.")
    title: str = Field(description="Human label, e.g. '1 · Extract claims'.")
    kind: StageKind
    ok: bool = True
    error: Optional[str] = None

    # The model call, when there is one (kind != 'code').
    model: Optional[str] = None
    system_prompt: Optional[str] = Field(default=None, description="Verbatim system message.")
    user_message: Optional[str] = Field(default=None, description="Verbatim rendered user message.")

    # The logical input the orchestrator passed, and the stage's output — both
    # arbitrary JSON so the screen can render anything, no matter how long.
    input: Any = None
    output: Any = None

    # Extras for the agentic (web) stage.
    sources: List[str] = Field(default_factory=list)
    web_steps: Any = None

    duration_ms: int = 0


class PipelineDiagnostics(BaseModel):
    """The full trace of a single run, every stage in order."""

    pipeline: str = "v3-best-of-both"
    article_title: str = ""
    stages: List[StageRecord] = Field(default_factory=list)
    total_ms: int = 0


class AnalyzeResult(BaseModel):
    """What the v3 endpoint returns: the report plus the complete diagnostics."""

    report: BoeReport
    diagnostics: PipelineDiagnostics
