import { useState } from 'react'
import type { DimensionAssessment, PlannedDimension } from '../types/analysis'
import { leanLabel, scoreColor, scoreTrackColor, severityBadge } from '../lib/ui'

export default function DimensionCard({
  a,
  planned,
}: {
  a: DimensionAssessment
  planned?: PlannedDimension
}) {
  const [open, setOpen] = useState(false)

  return (
    <div className="animate-fade-in rounded-xl border border-slate-200 bg-white shadow-sm">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-4 px-4 py-3 text-left"
      >
        <div
          className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-full text-sm font-bold text-white"
          style={{ background: scoreColor(a.score) }}
        >
          {a.score}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-800">{a.label}</span>
            <span
              className={`rounded-full px-2 py-0.5 text-xs font-medium ${severityBadge(a.severity)}`}
            >
              {a.severity}
            </span>
            {a.lean !== 'not-applicable' && a.lean !== 'undetermined' && (
              <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                leans {leanLabel(a.lean)}
              </span>
            )}
          </div>
          <p className="mt-0.5 truncate text-sm text-slate-500">{a.rationale}</p>
        </div>
        <span className="text-slate-400">{open ? '▲' : '▼'}</span>
      </button>

      <div className="px-4 pb-2">
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
          <div
            className={`h-full rounded-full ${scoreTrackColor(a.score)}`}
            style={{ width: `${a.score}%`, transition: 'width 0.6s ease' }}
          />
        </div>
      </div>

      {open && (
        <div className="space-y-4 border-t border-slate-100 px-4 py-4">
          {planned && (
            <div className="rounded-lg bg-indigo-50/60 p-3 text-sm">
              <p className="text-slate-700">
                <span className="font-semibold text-slate-600">Why this lens:</span>{' '}
                {planned.why_relevant}
              </p>
              {planned.focus && (
                <p className="mt-1 text-slate-700">
                  <span className="font-semibold text-slate-600">Focus:</span> {planned.focus}
                </p>
              )}
            </div>
          )}
          <p className="text-sm text-slate-700">{a.rationale}</p>

          {a.evidence.length > 0 && (
            <div>
              <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-400">
                Evidence
              </h4>
              <div className="space-y-2">
                {a.evidence.map((e, i) => (
                  <div key={i} className="rounded-lg bg-slate-50 p-3">
                    <p className="border-l-2 border-slate-300 pl-2 text-sm italic text-slate-700">
                      “{e.quote}”
                    </p>
                    <p className="mt-1 text-xs text-slate-500">{e.explanation}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {a.suggestions.length > 0 && (
            <div>
              <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-400">
                Suggestions
              </h4>
              <ul className="list-inside list-disc space-y-1 text-sm text-slate-700">
                {a.suggestions.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
