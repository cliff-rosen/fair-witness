"""Domain schemas for the fairness / bias analysis pipeline.

These are the business/domain objects shared across services and returned by
the orchestrator. They are deliberately the *single source of truth* for the
shapes that the LLM stages must emit (planner, dimension evaluators,
synthesizer) AND for what the API returns to the frontend.

Scoring convention (used everywhere):
    fairness score is an integer 0-100, where 100 = perfectly fair / unbiased
    and 0 = heavily biased. Higher is always better.
"""

import json
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


def _coerce_json_list(v: Any) -> Any:
    """Tolerate models that emit a list field as a JSON-encoded string.

    Claude's forced tool-use occasionally serializes a nested array-of-objects
    field as a string (e.g. evidence='[{...}]'). Parse it back to a list so the
    structured-output contract stays robust.
    """
    if isinstance(v, str):
        try:
            return json.loads(v)
        except (ValueError, TypeError):
            # Model emitted malformed JSON (e.g. a verbatim quote with an
            # unescaped inner quote). Fall back to a tolerant repair parse.
            try:
                from json_repair import repair_json

                repaired = repair_json(v, return_objects=True)
                if isinstance(repaired, (list, dict)):
                    return repaired
            except Exception:
                pass
            return v
    return v

# Stable catalogue of bias/fairness dimensions the system can evaluate.
# The planner chooses which subset is relevant for a given article.
DimensionKey = Literal[
    "loaded_language",
    "source_balance",
    "framing",
    "factual_selectivity",
    "omission",
    "tone_subjectivity",
    "attribution",
    "headline_accuracy",
]

SeverityLevel = Literal["none", "low", "moderate", "high"]

PoliticalLean = Literal[
    "left",
    "center-left",
    "center",
    "center-right",
    "right",
    "not-applicable",
    "undetermined",
]

FairnessLabel = Literal[
    "Highly Fair",
    "Mostly Fair",
    "Mixed",
    "Slanted",
    "Heavily Biased",
]

# How the topic itself is structured — lets the map stay honest about whether a
# topic is genuinely two-sided, settled, or not adversarial at all (guards
# against both manufactured false balance and false consensus).
IssueStructure = Literal[
    "settled",              # broad expert/factual consensus, vocal minority at most
    "genuinely-two-sided",  # two legitimate opposing positions
    "multi-sided",          # several legitimate positions
    "not-adversarial",      # not really a debate (e.g. human interest)
]

# Substantiation status of a side's talking point.
TalkingPointStatus = Literal[
    "substantiated",
    "partly-substantiated",
    "unsubstantiated",
    "contested",
]

ClaimType = Literal[
    "factual",
    "statistical",
    "causal",
    "predictive",
    "opinion",
    "value-judgment",
]

# How an article's claim relates to the independent issue map.
MapAlignment = Literal[
    "matches_settled_fact",
    "contradicts_settled_fact",
    "substantiated_argument",
    "unsubstantiated_talking_point",
    "novel_or_unverifiable",
]

# Whether the article handles the claim appropriately given its type/alignment.
ClaimHandling = Literal[
    "appropriate",          # presented in a way the evidence supports
    "appropriate_opinion",  # clearly-marked opinion, fair game
    "overstated",           # asserted more strongly than warranted
    "misleading",           # true-but-misleading / missing context
    "unsupported",          # asserted as fact without support
]


# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------

class ExtractedArticle(BaseModel):
    """The article text + metadata after ingestion (URL fetch or paste)."""

    title: str
    text: str
    source_url: Optional[str] = None
    byline: Optional[str] = None
    site_name: Optional[str] = Field(
        default=None, description="Publication / site name (e.g. 'Politico')."
    )
    published: Optional[str] = Field(
        default=None, description="Publication date as found on the page (raw string)."
    )
    note: Optional[str] = Field(
        default=None,
        description="Optional submitter note/context (shown on the report, not analyzed).",
    )
    word_count: int
    truncated: bool = Field(
        default=False,
        description="True if the body was truncated to fit the model budget.",
    )


# ===========================================================================
# v2 pipeline — EXTRACT stage (the shared "argument map" both rings run off).
# Captures WHAT the article argues + HOW its claims connect — never whether
# it's true. The high-load_bearing claims form the "spine" that Ring 1 checks.
# ===========================================================================

AsPresented = Literal["asserted", "attributed", "hedged"]


class ArgClaim(BaseModel):
    """One claim the article makes, placed in the argument structure."""

    id: str = Field(description="Short stable id, e.g. 'c1'.")
    text: str = Field(description="The claim as a tight paraphrase or short quote.")
    kind: ClaimType
    as_presented: AsPresented = Field(
        description="asserted (author's voice) / attributed (to a source) / hedged."
    )
    supports: List[str] = Field(
        default_factory=list,
        description="ids this claim backs — other claim ids and/or the literal 'thesis'.",
    )
    load_bearing: int = Field(
        ge=0, le=100,
        description="How central to the thesis (100 = the argument collapses without it).",
    )


class ArgumentMap(BaseModel):
    """The article's argument, structurally — not a truth judgment."""

    genre: str = Field(description="news report, op-ed, analysis, feature, blog, …")
    topic: str
    main_subject: str = Field(description="The central person/org/event covered.")
    summary: str = Field(description="2–3 sentence neutral summary.")
    thesis: str = Field(
        description="The central point the piece advances (for straight news, its main takeaway/frame)."
    )
    claims: List[ArgClaim] = Field(
        default_factory=list,
        description="The article's claims, with how they connect into the argument.",
    )

    @field_validator("claims", mode="before")
    @classmethod
    def _coerce(cls, v: Any) -> Any:
        return _coerce_json_list(v)


# ===========================================================================
# v2 pipeline — RING 0 (internal / coherence). Text-only: these consume the
# article + ArgumentMap and judge it ON ITS OWN TERMS — no outside facts.
# ===========================================================================

LogicIssueKind = Literal[
    "gap",                # conclusion the claims don't establish
    "contradiction",      # the piece contradicts itself
    "unsupported_leap",   # jump not backed by a stated claim
    "circular_reasoning",
    "non_sequitur",
    "overgeneralization",
    "missing_premise",
]


class LogicIssue(BaseModel):
    kind: LogicIssueKind
    detail: str = Field(description="What's wrong, in one sentence.")
    claim_ids: List[str] = Field(
        default_factory=list, description="Argument-map claim ids involved."
    )


class CoherenceAssessment(BaseModel):
    """Ring 0 · does the argument hold together on its own terms?"""

    score: int = Field(ge=0, le=100, description="Internal coherence (100 = airtight GIVEN its claims).")
    thesis_follows: bool = Field(description="Does the thesis follow from the supporting claims as presented?")
    closes_loop: bool = Field(description="Does it resolve what it raises (A→Z), not leave its central question dangling?")
    issues: List[LogicIssue] = Field(default_factory=list)
    rationale: str

    @field_validator("issues", mode="before")
    @classmethod
    def _coerce(cls, v: Any) -> Any:
        return _coerce_json_list(v)


class RhetoricFinding(BaseModel):
    quote: str = Field(description="Verbatim span from the article.")
    issue: str = Field(description="Why it's loaded / editorializing.")
    severity: SeverityLevel


class RhetoricAssessment(BaseModel):
    """Ring 0 · the manner — loaded language, tone, editorializing."""

    score: int = Field(ge=0, le=100, description="Neutrality of language (100 = measured, even-handed).")
    tone: str = Field(description="One or two words, e.g. 'measured', 'polemical', 'snarky'.")
    findings: List[RhetoricFinding] = Field(default_factory=list)
    rationale: str

    @field_validator("findings", mode="before")
    @classmethod
    def _coerce(cls, v: Any) -> Any:
        return _coerce_json_list(v)


class StructuralAssessment(BaseModel):
    """Ring 0 · internal self-consistency (headline↔body, attribution, opinion/fact)."""

    score: int = Field(ge=0, le=100, description="Self-consistency (100 = headline matches body, claims sourced, opinion separated).")
    headline_matches_body: bool
    headline_note: str = Field(default="", description="How the headline/lede relate to what the body supports.")
    contested_claims_attributed: bool = Field(
        description="Are contested claims sourced, vs asserted in the author's own voice?"
    )
    opinion_fact_separation: bool = Field(
        description="Is opinion kept distinct from reporting (judged genre-appropriately)?"
    )
    findings: List[str] = Field(default_factory=list, description="Specific self-consistency observations.")
    rationale: str

    @field_validator("findings", mode="before")
    @classmethod
    def _coerce(cls, v: Any) -> Any:
        return _coerce_json_list(v)


# ===========================================================================
# v2 pipeline — RING 1 (external / correspondence). Agentic: these SEARCH THE
# WEB and judge the article against reality, carrying their own source URLs.
# Seeded by the argument SPINE (the top load-bearing claims).
# ===========================================================================

class WebStep(BaseModel):
    """One step a Ring 1 agent took — a search query or a page fetch. The
    'relevant bits of search history' surfaced to the user as receipts."""

    kind: Literal["search", "fetch"]
    query: Optional[str] = None       # for search
    result_count: Optional[int] = None  # for search
    url: Optional[str] = None         # for fetch
    title: Optional[str] = None       # for fetch


EvidenceStance = Literal["supports", "contradicts", "contextualizes"]


class Evidence(BaseModel):
    """A specific retrieved quote tied to an assertion — the claim→evidence→source link."""

    source_url: str
    quote: str = Field(
        description="SHORT verbatim quote copied EXACTLY from the source that bears on the assertion."
    )
    stance: EvidenceStance = Field(
        description="Whether the quote supports, contradicts, or merely contextualizes the assertion."
    )
    verified: bool = Field(
        default=False,
        description="Set by code: true iff the quote actually appears in retrieved text. Leave false.",
    )


ClaimVerdict = Literal[
    "supported", "mostly_supported", "mixed", "contradicted", "unsupported", "unverifiable"
]
ClaimHandling = Literal["appropriate", "overstated", "missing_context", "misleading", "outdated"]


class ClaimCheck(BaseModel):
    """One spine claim, reality-checked against web evidence."""

    claim_id: str = Field(default="", description="Set by the agent from the argument map.")
    claim: str = Field(default="", description="Set by the agent.")
    verdict: ClaimVerdict = Field(description="How the claim holds up against the evidence found.")
    handling: ClaimHandling = Field(description="How the article handles the claim given that evidence.")
    finding: str = Field(description="1–2 sentences: what the evidence actually shows.")
    evidence: List[Evidence] = Field(
        default_factory=list, description="Quotes (source + verbatim quote + stance) backing the verdict."
    )
    sources: List[str] = Field(default_factory=list, description="All URLs consulted (set by the agent — leave empty).")
    trace: List[WebStep] = Field(default_factory=list, description="Search/fetch steps (set by the agent — leave empty).")

    @field_validator("evidence", mode="before")
    @classmethod
    def _coerce(cls, v: Any) -> Any:
        return _coerce_json_list(v)


FactStatus = Literal["established", "contested", "emerging", "disputed"]


class GroundedFact(BaseModel):
    fact: str
    status: FactStatus
    evidence: List[Evidence] = Field(default_factory=list, description="Source + verbatim quote backing the fact.")

    @field_validator("evidence", mode="before")
    @classmethod
    def _coerce(cls, v: Any) -> Any:
        return _coerce_json_list(v)


class RealityModel(BaseModel):
    """A web-grounded map of the topic — the yardstick the article is diffed against."""

    topic: str
    structure: IssueStructure
    structure_note: str
    key_facts: List[GroundedFact] = Field(default_factory=list)
    main_perspectives: List[str] = Field(default_factory=list, description="The legitimate positions in the debate.")
    common_distortions: List[str] = Field(default_factory=list, description="How coverage of this topic typically skews.")
    sources: List[str] = Field(default_factory=list)
    trace: List[WebStep] = Field(default_factory=list, description="Search/fetch steps (set by the agent — leave empty).")

    @field_validator("key_facts", "main_perspectives", "common_distortions", mode="before")
    @classmethod
    def _coerce(cls, v: Any) -> Any:
        return _coerce_json_list(v)


class Omission(BaseModel):
    missing: str = Field(description="What relevant fact/perspective/stakeholder is absent.")
    why_it_matters: str
    severity: SeverityLevel


class OmissionAssessment(BaseModel):
    """What the article left out / whose frame it adopted, vs the grounded reality model."""

    score: int = Field(ge=0, le=100, description="Coverage completeness (100 = nothing material omitted).")
    omissions: List[Omission] = Field(default_factory=list)
    adopted_framing: str = Field(default="", description="Whose framing the article adopts (or 'balanced').")
    both_sidesing: bool = Field(default=False, description="Treats a settled question as a live two-sided debate.")
    false_consensus: bool = Field(default=False, description="Presents a genuinely contested point as settled.")
    rationale: str

    @field_validator("omissions", mode="before")
    @classmethod
    def _coerce(cls, v: Any) -> Any:
        return _coerce_json_list(v)


# ===========================================================================
# v2 pipeline — SYNTHESIS + assembled report.
# ===========================================================================

class Verdict(BaseModel):
    """Two-axis verdict: coherence (Ring 0, internal) vs correspondence (Ring 1)."""

    coherence_score: int = Field(
        ge=0, le=100,
        description="Ring 0 — internal quality (logic, rhetoric, self-consistency). Text-grounded, high confidence.",
    )
    correspondence_score: int = Field(
        ge=0, le=100,
        description="Ring 1 — how it holds up against reality (claims + omissions). Only as strong as what was actually verified.",
    )
    overall_score: int = Field(ge=0, le=100, description="Reasoned blend (NOT an average).")
    fairness_label: FairnessLabel
    political_lean: PoliticalLean
    lean_confidence: int = Field(ge=0, le=100)
    both_sidesing: bool = False
    false_consensus: bool = False
    executive_summary: str
    key_strengths: List[str] = Field(default_factory=list)
    key_concerns: List[str] = Field(default_factory=list)

    @field_validator("key_strengths", "key_concerns", mode="before")
    @classmethod
    def _coerce(cls, v: Any) -> Any:
        return _coerce_json_list(v)


class Ring0Result(BaseModel):
    """Internal assessment — judged on the article's own terms (text-only)."""

    coherence: CoherenceAssessment
    rhetoric: RhetoricAssessment
    structural: StructuralAssessment


class Ring1Result(BaseModel):
    """External assessment — judged against reality (web-grounded)."""

    reality: RealityModel
    claim_checks: List[ClaimCheck] = Field(default_factory=list)
    omission: OmissionAssessment


class FairnessReport(BaseModel):
    """The complete v2 report: extract → ring0 ∥ ring1 → verdict."""

    article: ExtractedArticle
    argument: ArgumentMap
    ring0: Ring0Result
    ring1: Ring1Result
    verdict: Verdict
    report_id: Optional[str] = Field(default=None, description="Share id; present only on stored reports.")
    created_at: Optional[str] = None


# ---------------------------------------------------------------------------
# Stage 1 — Planner
# ---------------------------------------------------------------------------

class PlannedDimension(BaseModel):
    """One dimension the planner selected, with a focus hint for its evaluator."""

    key: DimensionKey
    label: str = Field(description="Human-readable dimension name.")
    why_relevant: str = Field(description="Why this dimension matters for THIS article.")
    focus: str = Field(description="Specific thing the evaluator should look hardest at.")


class AnalysisPlan(BaseModel):
    """Output of the planner: what the article is, and how to evaluate it."""

    article_type: str = Field(description="e.g. news report, op-ed, feature, analysis, blog.")
    topic: str = Field(description="Primary subject matter of the article.")
    main_subject: str = Field(description="The central person/org/event being covered.")
    summary: str = Field(description="2-3 sentence neutral summary of the article.")
    central_claims: List[str] = Field(
        default_factory=list,
        description="The key factual claims or assertions the article makes.",
    )
    dimensions: List[PlannedDimension] = Field(
        description="The bias/fairness dimensions to evaluate, most relevant first.",
    )

    @field_validator("central_claims", "dimensions", mode="before")
    @classmethod
    def _coerce(cls, v: Any) -> Any:
        return _coerce_json_list(v)


# ---------------------------------------------------------------------------
# Stage 2 — Issue Map (built BLIND to the article, from the topic alone)
# ---------------------------------------------------------------------------

class TalkingPoint(BaseModel):
    """A rhetorical point a side typically makes, with its substantiation."""

    point: str
    status: TalkingPointStatus


class IssueSide(BaseModel):
    """One recognized position in the debate around the topic."""

    name: str = Field(description="Short label for the side/position.")
    position: str = Field(description="One-sentence summary of what this side holds.")
    typical_arguments: List[str] = Field(
        default_factory=list,
        description="The strongest arguments this side typically makes.",
    )
    talking_points: List[TalkingPoint] = Field(
        default_factory=list,
        description="Common talking points / rhetoric, flagged by substantiation.",
    )

    @field_validator("typical_arguments", "talking_points", mode="before")
    @classmethod
    def _coerce(cls, v: Any) -> Any:
        return _coerce_json_list(v)


class SettledFact(BaseModel):
    """A fact widely treated as established on this topic."""

    fact: str
    confidence: int = Field(ge=0, le=100, description="How settled this is (100 = beyond dispute).")


class IssueMap(BaseModel):
    """An independent map of the debate around the topic.

    Generated from the topic alone, WITHOUT seeing the article, so it can serve
    as a neutral reference frame: the article is later diffed against it to spot
    omission, selectivity, adopted framing, and both-sidesing / false consensus.
    """

    topic: str
    structure: IssueStructure = Field(description="How the topic is actually structured.")
    structure_note: str = Field(
        description="Explanation of the structure; flag if the topic is NOT genuinely two-sided.",
    )
    sides: List[IssueSide] = Field(
        default_factory=list,
        description="The recognized positions in the debate.",
    )
    settled_facts: List[SettledFact] = Field(
        default_factory=list,
        description="Facts widely treated as established, regardless of side.",
    )
    common_biases: List[str] = Field(
        default_factory=list,
        description="Biases / slants articles on this topic typically exhibit.",
    )

    @field_validator("sides", "settled_facts", "common_biases", mode="before")
    @classmethod
    def _coerce(cls, v: Any) -> Any:
        return _coerce_json_list(v)


# ---------------------------------------------------------------------------
# Stage 3 — Dimension evaluators (fan-out)
# ---------------------------------------------------------------------------

class EvidenceQuote(BaseModel):
    """A specific span from the article that supports a finding."""

    quote: str = Field(description="Verbatim (or lightly trimmed) quote from the article.")
    explanation: str = Field(
        default="", description="Why this quote demonstrates the issue."
    )


class DimensionAssessment(BaseModel):
    """One specialized evaluator's verdict on a single dimension."""

    key: DimensionKey
    label: str
    score: int = Field(ge=0, le=100, description="Fairness on this dimension (100 = unbiased).")
    severity: SeverityLevel = Field(description="Severity of the bias concern found.")
    lean: PoliticalLean = Field(
        default="not-applicable",
        description="Direction the bias on this dimension leans, if any.",
    )
    rationale: str = Field(description="Concise explanation of the score.")
    evidence: List[EvidenceQuote] = Field(
        default_factory=list,
        description="Concrete quotes supporting the assessment.",
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Actionable edits that would make the article fairer.",
    )

    @field_validator("evidence", "suggestions", mode="before")
    @classmethod
    def _coerce(cls, v: Any) -> Any:
        return _coerce_json_list(v)


# ---------------------------------------------------------------------------
# Stage 4 — Claim analysis (article claims diffed against the issue map)
# ---------------------------------------------------------------------------

class ClaimAssessment(BaseModel):
    """One article claim, located against the independent issue map."""

    claim: str = Field(description="The claim, as a short quote or tight paraphrase.")
    claim_type: ClaimType
    centrality: int = Field(ge=0, le=100, description="How load-bearing to the article's thesis.")
    as_presented: str = Field(
        description="How the article presents it (e.g. stated as fact / attributed / hedged).",
    )
    map_alignment: MapAlignment = Field(description="How it relates to the issue map.")
    handling: ClaimHandling = Field(description="Whether the article handles it appropriately.")
    note: str = Field(description="Brief explanation of the alignment/handling call.")


class ClaimAnalysis(BaseModel):
    """Wrapper so the claim analyst can emit a list under forced tool-use."""

    claims: List[ClaimAssessment] = Field(default_factory=list)

    @field_validator("claims", mode="before")
    @classmethod
    def _coerce(cls, v: Any) -> Any:
        return _coerce_json_list(v)


# ---------------------------------------------------------------------------
# Stage 5 — Synthesizer + final report
# ---------------------------------------------------------------------------

class OverallAssessment(BaseModel):
    """The synthesizer's holistic, two-axis verdict."""

    overall_score: int = Field(ge=0, le=100, description="Blended overall fairness (100 = fair).")
    presentation_score: int = Field(
        ge=0, le=100, description="HOW it says it: language, framing, tone, balance (100 = fair).",
    )
    substantive_score: int = Field(
        ge=0, le=100, description="WHAT it says: claims, facts, coverage vs the map (100 = fair).",
    )
    fairness_label: FairnessLabel
    political_lean: PoliticalLean
    lean_confidence: int = Field(ge=0, le=100, description="Confidence in the lean call.")
    adopted_framing: str = Field(
        default="",
        description="Whose framing the article adopts, relative to the issue map (or 'balanced').",
    )
    both_sidesing: bool = Field(
        default=False,
        description="True if the article presents a settled question as a live two-sided debate.",
    )
    false_consensus: bool = Field(
        default=False,
        description="True if the article presents a genuinely contested point as settled.",
    )
    executive_summary: str = Field(description="Plain-language verdict for a reader.")
    key_strengths: List[str] = Field(default_factory=list)
    key_concerns: List[str] = Field(default_factory=list)

    @field_validator("key_strengths", "key_concerns", mode="before")
    @classmethod
    def _coerce(cls, v: Any) -> Any:
        return _coerce_json_list(v)


class BiasReport(BaseModel):
    """The complete, assembled report returned by the orchestrator."""

    article: ExtractedArticle
    plan: AnalysisPlan
    issue_map: IssueMap
    dimensions: List[DimensionAssessment]
    claims: List[ClaimAssessment]
    overall: OverallAssessment

    # Set once the report is persisted for sharing (see services/report_repository.py).
    report_id: Optional[str] = Field(
        default=None, description="Unguessable share id; present only on stored reports."
    )
    created_at: Optional[str] = Field(
        default=None, description="UTC ISO-8601 timestamp when the report was stored."
    )
