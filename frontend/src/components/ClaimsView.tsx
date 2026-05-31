import type { ClaimAssessment } from '../types/analysis'
import { handlingMeta, mapAlignmentMeta } from '../lib/ui'

/** Renders the article's claims, each located against the issue map. */
export default function ClaimsView({ claims }: { claims: ClaimAssessment[] }) {
  // Most material first.
  const sorted = [...claims].sort((a, b) => b.centrality - a.centrality)

  return (
    <div className="space-y-2">
      {sorted.map((c, i) => {
        const align = mapAlignmentMeta(c.map_alignment)
        const handling = handlingMeta(c.handling)
        return (
          <div
            key={i}
            className="animate-fade-in rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
          >
            <div className="flex items-start justify-between gap-3">
              <p className="text-sm font-medium text-slate-800">“{c.claim}”</p>
              <span className="flex-shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
                {c.claim_type}
              </span>
            </div>
            <div className="mt-2 flex flex-wrap items-center gap-1.5">
              <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${align.cls}`}>
                {align.label}
              </span>
              <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${handling.cls}`}>
                {handling.label}
              </span>
              <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
                {c.as_presented}
              </span>
              <span
                className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-500"
                title="How load-bearing this claim is to the article's thesis (0–100)"
              >
                centrality {c.centrality}
              </span>
            </div>
            <p className="mt-2 text-sm text-slate-600">{c.note}</p>
          </div>
        )
      })}
    </div>
  )
}
