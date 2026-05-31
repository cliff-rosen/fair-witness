import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getReport } from '../lib/api/reportApi'
import ReportView from '../components/ReportView'
import ShareBar from '../components/ShareBar'
import type { FairnessReport } from '../types/analysis'

type Status = 'loading' | 'ok' | 'notfound' | 'error'

/**
 * Public, read-only view of a stored report at /r/:id. Never prompts for the
 * passphrase — anyone with the link can open it.
 */
export default function ReportPage() {
  const { id } = useParams<{ id: string }>()
  const [report, setReport] = useState<FairnessReport | null>(null)
  const [status, setStatus] = useState<Status>('loading')

  useEffect(() => {
    if (!id) {
      setStatus('notfound')
      return
    }
    let alive = true
    setStatus('loading')
    getReport(id)
      .then((r) => {
        if (!alive) return
        setReport(r)
        setStatus('ok')
      })
      .catch((e) => {
        if (!alive) return
        setStatus(e?.response?.status === 404 ? 'notfound' : 'error')
      })
    return () => {
      alive = false
    }
  }, [id])

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <header className="mb-6 flex items-center justify-between">
        <p className="text-sm font-medium uppercase tracking-wide text-slate-400">
          Shared fairness &amp; bias report
        </p>
        <Link
          to="/"
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700"
        >
          Analyze an article
        </Link>
      </header>

      {status === 'loading' && (
        <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center text-slate-500 shadow-sm">
          Loading report…
        </div>
      )}

      {status === 'notfound' && (
        <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center shadow-sm">
          <p className="text-lg font-semibold text-slate-700">Report not found</p>
          <p className="mt-1 text-sm text-slate-500">
            This link may be mistyped or the report may no longer exist.
          </p>
        </div>
      )}

      {status === 'error' && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-10 text-center shadow-sm">
          <p className="text-lg font-semibold text-red-700">Couldn’t load this report</p>
          <p className="mt-1 text-sm text-red-600">Please try again in a moment.</p>
        </div>
      )}

      {status === 'ok' && report && (
        <div className="space-y-4">
          {id && <ShareBar reportId={id} />}
          <ReportView report={report} />
        </div>
      )}
    </div>
  )
}
