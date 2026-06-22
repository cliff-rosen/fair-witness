/** Types for the analyze pipeline + its diagnostics. Mirrors backend/schemas/analyze.py. */

export type AsPresented = 'asserted' | 'attributed' | 'hedged'
export type IssueStructure = 'settled' | 'genuinely-two-sided' | 'multi-sided' | 'not-adversarial'
export type Substantiation = 'substantiated' | 'partly-substantiated' | 'contested' | 'unsubstantiated'
export type ClaimLocation =
  | 'matches_settled_fact'
  | 'contradicts_settled_fact'
  | 'substantiated_argument'
  | 'unsubstantiated_talking_point'
  | 'novel_or_unverifiable'
export type ClaimHandling = 'fair' | 'overstated' | 'asserted_as_fact' | 'missing_context' | 'misleading'
export type FairnessLabel = 'Highly Fair' | 'Mostly Fair' | 'Mixed' | 'Slanted' | 'Heavily Biased'

export interface Claim {
  id: string
  text: string
  as_presented: AsPresented
  centrality: number
}

export interface ClaimSet {
  genre: string
  topic: string
  main_subject: string
  summary: string
  thesis: string
  claims: Claim[]
}

export interface TalkingPoint {
  point: string
  substantiation: Substantiation
}
export interface Side {
  name: string
  position: string
  talking_points: TalkingPoint[]
}
export interface SettledFact {
  fact: string
  source_url?: string | null
  confidence: number
}
export interface TopicMap {
  topic: string
  structure: IssueStructure
  structure_note: string
  sides: Side[]
  settled_facts: SettledFact[]
  common_biases: string[]
  sources: string[]
}

export interface ClaimPlacement {
  claim_id: string
  claim: string
  location: ClaimLocation
  side: string
  handling: ClaimHandling
  note: string
  source_quote: string
  source_url: string
}

export interface Verdict {
  substantive_score: number
  presentation_score: number
  overall_score: number
  fairness_label: FairnessLabel
  both_sidesing: boolean
  false_consensus: boolean
  summary: string
  strengths: string[]
  concerns: string[]
}

export interface AnalyzeReport {
  article: { title: string; text: string; word_count: number; site_name?: string | null; byline?: string | null }
  claims: ClaimSet
  topic_map: TopicMap
  placements: ClaimPlacement[]
  verdict: Verdict
  report_id?: string | null
  created_at?: string | null
}

export type StageKind = 'code' | 'structured' | 'agentic'

export interface WebStep {
  kind: 'search' | 'fetch'
  query?: string | null
  result_count?: number | null
  url?: string | null
  title?: string | null
}

export interface StageRecord {
  name: string
  title: string
  kind: StageKind
  ok: boolean
  error?: string | null
  model?: string | null
  system_prompt?: string | null
  user_message?: string | null
  input: unknown
  output: unknown
  sources: string[]
  web_steps?: WebStep[] | null
  duration_ms: number
}

export interface PipelineDiagnostics {
  pipeline: string
  article_title: string
  stages: StageRecord[]
  total_ms: number
}

export interface AnalyzeResult {
  report: AnalyzeReport
  diagnostics: PipelineDiagnostics
}
