// Domain types — mirror backend/schemas/analysis.py (single source of truth).
// Scoring convention: integer 0-100, where 100 = perfectly fair / unbiased.

export type SeverityLevel = 'none' | 'low' | 'moderate' | 'high'

export type PoliticalLean =
  | 'left'
  | 'center-left'
  | 'center'
  | 'center-right'
  | 'right'
  | 'not-applicable'
  | 'undetermined'

export type FairnessLabel =
  | 'Highly Fair'
  | 'Mostly Fair'
  | 'Mixed'
  | 'Slanted'
  | 'Heavily Biased'

export type IssueStructure =
  | 'settled'
  | 'genuinely-two-sided'
  | 'multi-sided'
  | 'not-adversarial'

// Used by presentation helpers in lib/ui.ts.
export type TalkingPointStatus =
  | 'substantiated'
  | 'partly-substantiated'
  | 'unsubstantiated'
  | 'contested'

export type ClaimType =
  | 'factual'
  | 'statistical'
  | 'causal'
  | 'predictive'
  | 'opinion'
  | 'value-judgment'

// Used by presentation helpers in lib/ui.ts.
export type MapAlignment =
  | 'matches_settled_fact'
  | 'contradicts_settled_fact'
  | 'substantiated_argument'
  | 'unsubstantiated_talking_point'
  | 'novel_or_unverifiable'

// Used by presentation helpers in lib/ui.ts.
export type ClaimHandling =
  | 'appropriate'
  | 'appropriate_opinion'
  | 'overstated'
  | 'misleading'
  | 'unsupported'

export interface ExtractedArticle {
  title: string
  text: string
  source_url: string | null
  byline: string | null
  site_name: string | null
  published: string | null
  note: string | null
  word_count: number
  truncated: boolean
}

// Lightweight metadata for feed/card listings (Recent, Highlights).
export interface ReportSummary {
  report_id: string
  title: string
  topic: string
  overall_score: number
  fairness_label: FairnessLabel
  political_lean: PoliticalLean
  created_at?: string | null
}

// ===========================================================================
// Two-ring pipeline types — mirror backend/schemas/analysis.py
// ===========================================================================

export type AsPresented = 'asserted' | 'attributed' | 'hedged'

export interface ArgClaim {
  id: string
  text: string
  kind: ClaimType
  as_presented: AsPresented
  supports: string[]
  load_bearing: number
}

export interface ArgumentMap {
  genre: string
  topic: string
  main_subject: string
  summary: string
  thesis: string
  claims: ArgClaim[]
}

export type LogicIssueKind =
  | 'gap' | 'contradiction' | 'unsupported_leap' | 'circular_reasoning'
  | 'non_sequitur' | 'overgeneralization' | 'missing_premise'

export interface LogicIssue {
  kind: LogicIssueKind
  detail: string
  claim_ids: string[]
}

export interface CoherenceAssessment {
  score: number
  thesis_follows: boolean
  closes_loop: boolean
  issues: LogicIssue[]
  rationale: string
}

export interface RhetoricFinding {
  quote: string
  issue: string
  severity: SeverityLevel
}

export interface RhetoricAssessment {
  score: number
  tone: string
  findings: RhetoricFinding[]
  rationale: string
}

export interface StructuralAssessment {
  score: number
  headline_matches_body: boolean
  headline_note: string
  contested_claims_attributed: boolean
  opinion_fact_separation: boolean
  findings: string[]
  rationale: string
}

export type EvidenceStance = 'supports' | 'contradicts' | 'contextualizes'

export interface Evidence {
  source_url: string
  quote: string
  stance: EvidenceStance
  verified: boolean
}

export interface WebStep {
  kind: 'search' | 'fetch'
  query?: string | null
  result_count?: number | null
  url?: string | null
  title?: string | null
}

export type ClaimVerdict =
  | 'supported' | 'mostly_supported' | 'mixed' | 'contradicted' | 'unsupported' | 'unverifiable'
export type CheckHandling =
  | 'appropriate' | 'overstated' | 'missing_context' | 'misleading' | 'outdated'

export interface ClaimCheck {
  claim_id: string
  claim: string
  verdict: ClaimVerdict
  handling: CheckHandling
  finding: string
  evidence: Evidence[]
  sources: string[]
  trace: WebStep[]
}

export type FactStatus = 'established' | 'contested' | 'emerging' | 'disputed'

export interface GroundedFact {
  fact: string
  status: FactStatus
  evidence: Evidence[]
}

export interface RealityModel {
  topic: string
  structure: IssueStructure
  structure_note: string
  key_facts: GroundedFact[]
  main_perspectives: string[]
  common_distortions: string[]
  sources: string[]
  trace: WebStep[]
}

export interface Omission {
  missing: string
  why_it_matters: string
  severity: SeverityLevel
}

export interface OmissionAssessment {
  score: number
  omissions: Omission[]
  adopted_framing: string
  both_sidesing: boolean
  false_consensus: boolean
  rationale: string
}

export interface Verdict {
  coherence_score: number
  correspondence_score: number
  overall_score: number
  fairness_label: FairnessLabel
  political_lean: PoliticalLean
  lean_confidence: number
  both_sidesing: boolean
  false_consensus: boolean
  executive_summary: string
  key_strengths: string[]
  key_concerns: string[]
}

export interface Ring0Result {
  coherence: CoherenceAssessment
  rhetoric: RhetoricAssessment
  structural: StructuralAssessment
}

export interface Ring1Result {
  reality: RealityModel
  claim_checks: ClaimCheck[]
  omission: OmissionAssessment
}

export interface FairnessReport {
  article: ExtractedArticle
  argument: ArgumentMap
  ring0: Ring0Result
  ring1: Ring1Result
  verdict: Verdict
  report_id?: string | null
  created_at?: string | null
}

export type FairnessEventType =
  | 'ingested' | 'argument' | 'coherence' | 'rhetoric' | 'structural'
  | 'reality' | 'claim_check' | 'omission' | 'verdict' | 'report' | 'error'

export interface FairnessEvent {
  type: FairnessEventType
  message?: string | null
  article?: ExtractedArticle | null
  argument?: ArgumentMap | null
  coherence?: CoherenceAssessment | null
  rhetoric?: RhetoricAssessment | null
  structural?: StructuralAssessment | null
  reality?: RealityModel | null
  claim_check?: ClaimCheck | null
  omission?: OmissionAssessment | null
  verdict?: Verdict | null
  report?: FairnessReport | null
}
