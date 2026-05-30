import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getReport } from '../lib/api/reportApi'
import { HIGHLIGHT_REPORT_IDS } from '../lib/highlights'
import ReportCard from '../components/ReportCard'
import type { ReportSummary } from '../types/analysis'

export default function HighlightsPage() {
  const [reports, setReports] = useState<ReportSummary[]>([])
  const [loading, setLoading] = useState(HIGHLIGHT_REPORT_IDS.length > 0)

  useEffect(() => {
    if (HIGHLIGHT_REPORT_IDS.length === 0) return
    let alive = true
    // Fetch each curated report and map to a card summary. Missing ones are skipped.
    Promise.all(
      HIGHLIGHT_REPORT_IDS.map((id) =>
        getReport(id)
          .then((r): ReportSummary => ({
            report_id: r.report_id ?? id,
            title: r.article.title,
            topic: r.plan.topic,
            overall_score: r.overall.overall_score,
            fairness_label: r.overall.fairness_label,
            political_lean: r.overall.political_lean,
            created_at: r.created_at,
          }))
          .catch(() => null),
      ),
    )
      .then((rs) => alive && setReports(rs.filter((r): r is ReportSummary => r !== null)))
      .finally(() => alive && setLoading(false))
    return () => {
      alive = false
    }
  }, [])

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight text-slate-800">Highlights</h1>
        <p className="text-sm text-slate-500">A hand-picked selection of notable analyses.</p>
      </header>

      {loading ? (
        <p className="rounded-2xl border border-slate-200 bg-white p-10 text-center text-slate-500 shadow-sm">
          Loading…
        </p>
      ) : reports.length === 0 ? (
        <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center shadow-sm">
          <p className="text-lg font-semibold text-slate-700">Highlights coming soon</p>
          <p className="mt-1 text-sm text-slate-500">
            Curated standouts will appear here. In the meantime,{' '}
            <Link to="/" className="font-medium text-indigo-600 hover:underline">
              analyze an article
            </Link>{' '}
            or browse{' '}
            <Link to="/recent" className="font-medium text-indigo-600 hover:underline">
              recent ones
            </Link>
            .
          </p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {reports.map((r) => (
            <ReportCard key={r.report_id} report={r} />
          ))}
        </div>
      )}
    </div>
  )
}
