import { Link } from 'react-router-dom'
import type { ReportSummary } from '../types/analysis'
import { leanLabel, scoreColor } from '../lib/ui'

function formatDate(iso?: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d.getTime())) return ''
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

/** Compact card linking to a stored report — used by Recent and Highlights. */
export default function ReportCard({ report }: { report: ReportSummary }) {
  return (
    <Link
      to={`/r/${report.report_id}`}
      className="group flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-indigo-200 hover:shadow"
    >
      <div className="flex items-start justify-between gap-3">
        <h3 className="line-clamp-2 font-semibold text-slate-800 group-hover:text-indigo-700">
          {report.title}
        </h3>
        <div
          className="flex h-12 w-12 shrink-0 flex-col items-center justify-center rounded-full text-white"
          style={{ backgroundColor: scoreColor(report.overall_score) }}
          title="Overall fairness score"
        >
          <span className="text-lg font-bold leading-none">{report.overall_score}</span>
        </div>
      </div>
      {report.topic && <p className="line-clamp-2 text-sm text-slate-500">{report.topic}</p>}
      <div className="mt-auto flex flex-wrap items-center gap-2 text-xs text-slate-500">
        <span className="rounded-full bg-slate-100 px-2 py-0.5 font-medium text-slate-700">
          {report.fairness_label}
        </span>
        {report.political_lean !== 'not-applicable' && (
          <span className="rounded-full bg-slate-100 px-2 py-0.5">
            Lean: {leanLabel(report.political_lean)}
          </span>
        )}
        {report.created_at && <span className="ml-auto">{formatDate(report.created_at)}</span>}
      </div>
    </Link>
  )
}
