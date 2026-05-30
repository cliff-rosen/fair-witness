// Shared presentation helpers — score -> color, severity -> styling.
import type {
  SeverityLevel,
  PoliticalLean,
  TalkingPointStatus,
  MapAlignment,
  ClaimHandling,
  IssueStructure,
} from '../types/analysis'

export function scoreColor(score: number): string {
  if (score >= 80) return '#16a34a' // green-600
  if (score >= 60) return '#65a30d' // lime-600
  if (score >= 40) return '#d97706' // amber-600
  if (score >= 20) return '#ea580c' // orange-600
  return '#dc2626' // red-600
}

export function scoreTrackColor(score: number): string {
  if (score >= 80) return 'bg-green-500'
  if (score >= 60) return 'bg-lime-500'
  if (score >= 40) return 'bg-amber-500'
  if (score >= 20) return 'bg-orange-500'
  return 'bg-red-500'
}

export function severityBadge(severity: SeverityLevel): string {
  switch (severity) {
    case 'none':
      return 'bg-green-100 text-green-800'
    case 'low':
      return 'bg-lime-100 text-lime-800'
    case 'moderate':
      return 'bg-amber-100 text-amber-800'
    case 'high':
      return 'bg-red-100 text-red-800'
  }
}

export function leanLabel(lean: PoliticalLean): string {
  if (lean === 'not-applicable') return 'N/A'
  if (lean === 'undetermined') return 'Undetermined'
  return lean.replace('-', ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

export function structureLabel(s: IssueStructure): string {
  switch (s) {
    case 'settled':
      return 'Settled'
    case 'genuinely-two-sided':
      return 'Genuinely two-sided'
    case 'multi-sided':
      return 'Multi-sided'
    case 'not-adversarial':
      return 'Not a debate'
  }
}

export function talkingPointBadge(status: TalkingPointStatus): string {
  switch (status) {
    case 'substantiated':
      return 'bg-green-100 text-green-800'
    case 'partly-substantiated':
      return 'bg-lime-100 text-lime-800'
    case 'unsubstantiated':
      return 'bg-red-100 text-red-800'
    case 'contested':
      return 'bg-amber-100 text-amber-800'
  }
}

export function mapAlignmentMeta(a: MapAlignment): { label: string; cls: string } {
  switch (a) {
    case 'matches_settled_fact':
      return { label: 'matches settled fact', cls: 'bg-green-100 text-green-800' }
    case 'contradicts_settled_fact':
      return { label: 'contradicts settled fact', cls: 'bg-red-100 text-red-800' }
    case 'substantiated_argument':
      return { label: 'substantiated argument', cls: 'bg-lime-100 text-lime-800' }
    case 'unsubstantiated_talking_point':
      return { label: 'unsubstantiated talking point', cls: 'bg-amber-100 text-amber-800' }
    case 'novel_or_unverifiable':
      return { label: 'novel / unverifiable', cls: 'bg-slate-100 text-slate-700' }
  }
}

export function handlingMeta(h: ClaimHandling): { label: string; cls: string } {
  switch (h) {
    case 'appropriate':
      return { label: 'handled appropriately', cls: 'bg-green-100 text-green-800' }
    case 'appropriate_opinion':
      return { label: 'fair opinion', cls: 'bg-green-100 text-green-800' }
    case 'overstated':
      return { label: 'overstated', cls: 'bg-amber-100 text-amber-800' }
    case 'misleading':
      return { label: 'misleading', cls: 'bg-orange-100 text-orange-800' }
    case 'unsupported':
      return { label: 'unsupported', cls: 'bg-red-100 text-red-800' }
  }
}
