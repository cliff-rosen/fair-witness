import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listRecent } from '../lib/api/reportApi'
import ReportCard from '../components/ReportCard'
import type { ReportSummary } from '../types/analysis'

export default function RecentPage() {
  const [reports, setReports] = useState<ReportSummary[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let alive = true
    listRecent()
      .then((r) => alive && setReports(r))
      .catch(() => alive && setReports([]))
      .finally(() => alive && setLoading(false))
    return () => {
      alive = false
    }
  }, [])

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight text-slate-800">Recently analyzed</h1>
        <p className="text-sm text-slate-500">The latest articles run through Fair Witness.</p>
      </header>

      {loading ? (
        <p className="rounded-2xl border border-slate-200 bg-white p-10 text-center text-slate-500 shadow-sm">
          Loading…
        </p>
      ) : reports.length === 0 ? (
        <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center shadow-sm">
          <p className="text-lg font-semibold text-slate-700">Nothing here yet</p>
          <p className="mt-1 text-sm text-slate-500">
            Be the first —{' '}
            <Link to="/" className="font-medium text-indigo-600 hover:underline">
              analyze an article
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
