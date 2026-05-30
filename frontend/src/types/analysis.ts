// Domain types — mirror backend/schemas/analysis.py (single source of truth).
// Scoring convention: integer 0-100, where 100 = perfectly fair / unbiased.

export type DimensionKey =
  | 'loaded_language'
  | 'source_balance'
  | 'framing'
  | 'factual_selectivity'
  | 'omission'
  | 'tone_subjectivity'
  | 'attribution'
  | 'headline_accuracy'

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

export type MapAlignment =
  | 'matches_settled_fact'
  | 'contradicts_settled_fact'
  | 'substantiated_argument'
  | 'unsubstantiated_talking_point'
  | 'novel_or_unverifiable'

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
  word_count: number
  truncated: boolean
}

export interface PlannedDimension {
  key: DimensionKey
  label: string
  why_relevant: string
  focus: string
}

export interface AnalysisPlan {
  article_type: string
  topic: string
  main_subject: string
  summary: string
  central_claims: string[]
  dimensions: PlannedDimension[]
}

export interface TalkingPoint {
  point: string
  status: TalkingPointStatus
}

export interface IssueSide {
  name: string
  position: string
  typical_arguments: string[]
  talking_points: TalkingPoint[]
}

export interface SettledFact {
  fact: string
  confidence: number
}

export interface IssueMap {
  topic: string
  structure: IssueStructure
  structure_note: string
  sides: IssueSide[]
  settled_facts: SettledFact[]
  common_biases: string[]
}

export interface ClaimAssessment {
  claim: string
  claim_type: ClaimType
  centrality: number
  as_presented: string
  map_alignment: MapAlignment
  handling: ClaimHandling
  note: string
}

export interface EvidenceQuote {
  quote: string
  explanation: string
}

export interface DimensionAssessment {
  key: DimensionKey
  label: string
  score: number
  severity: SeverityLevel
  lean: PoliticalLean
  rationale: string
  evidence: EvidenceQuote[]
  suggestions: string[]
}

export interface OverallAssessment {
  overall_score: number
  presentation_score: number
  substantive_score: number
  fairness_label: FairnessLabel
  political_lean: PoliticalLean
  lean_confidence: number
  adopted_framing: string
  both_sidesing: boolean
  false_consensus: boolean
  executive_summary: string
  key_strengths: string[]
  key_concerns: string[]
}

export interface BiasReport {
  article: ExtractedArticle
  plan: AnalysisPlan
  issue_map: IssueMap
  dimensions: DimensionAssessment[]
  claims: ClaimAssessment[]
  overall: OverallAssessment
}

// --- Streaming events (mirror backend/schemas/events.py) ---

export type AnalysisEventType =
  | 'ingested'
  | 'plan'
  | 'issue_map'
  | 'dimensions_planned'
  | 'dimension_complete'
  | 'claims_analyzed'
  | 'synthesizing'
  | 'report'
  | 'error'

export interface AnalysisEvent {
  type: AnalysisEventType
  message?: string | null
  article?: ExtractedArticle | null
  plan?: AnalysisPlan | null
  issue_map?: IssueMap | null
  dimensions?: PlannedDimension[] | null
  assessment?: DimensionAssessment | null
  claims?: ClaimAssessment[] | null
  report?: BiasReport | null
}
