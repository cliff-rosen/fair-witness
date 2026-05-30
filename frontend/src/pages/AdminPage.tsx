import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getAdminOverview, type AdminOverview } from '../lib/api/adminApi'
import { clearAdminPassword, getAdminPassword, setAdminPassword } from '../lib/adminAuth'

type Status = 'need-auth' | 'loading' | 'ok' | 'error'

function StatCard({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="text-2xl font-bold text-slate-800">{value}</div>
      <div className="text-xs uppercase tracking-wide text-slate-400">{label}</div>
    </div>
  )
}

function fmtTs(iso: string | null) {
  if (!iso) return ''
  const d = new Date(iso)
  return isNaN(d.getTime()) ? iso : d.toLocaleString()
}

export default function AdminPage() {
  const [pw, setPw] = useState('')
  const [data, setData] = useState<AdminOverview | null>(null)
  const [status, setStatus] = useState<Status>(getAdminPassword() ? 'loading' : 'need-auth')
  const [err, setErr] = useState<string | null>(null)

  async function load() {
    setStatus('loading')
    setErr(null)
    try {
      setData(await getAdminOverview())
      setStatus('ok')
    } catch (e: any) {
      const code = e?.response?.status
      if (code === 401) {
        clearAdminPassword()
        setStatus('need-auth')
        setErr('Incorrect admin password.')
      } else if (code === 404) {
        setStatus('error')
        setErr('Admin is not configured on the server (ADMIN_PASSWORD unset).')
      } else {
        setStatus('error')
        setErr('Could not load admin data.')
      }
    }
  }

  useEffect(() => {
    if (getAdminPassword()) load()
  }, [])

  function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!pw.trim()) return
    setAdminPassword(pw.trim())
    load()
  }

  if (status === 'need-auth' || status === 'error') {
    return (
      <div className="mx-auto max-w-sm px-4 py-16">
        <h1 className="text-xl font-bold text-slate-800">Admin</h1>
        <p className="mt-1 text-sm text-slate-500">Enter the admin password to view tracking.</p>
        <form onSubmit={submit} className="mt-4">
          <input
            autoFocus
            type="password"
            value={pw}
            onChange={(e) => setPw(e.target.value)}
            placeholder="Admin password"
            className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          />
          {err && <p className="mt-2 text-sm text-red-600">{err}</p>}
          <button
            type="submit"
            className="mt-3 w-full rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700"
          >
            Unlock
          </button>
        </form>
      </div>
    )
  }

  if (status === 'loading' || !data) {
    return <div className="mx-auto max-w-5xl px-4 py-16 text-center text-slate-500">Loading…</div>
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight text-slate-800">Tracking</h1>
        <div className="flex items-center gap-3 text-sm">
          <button onClick={load} className="text-indigo-600 hover:underline">
            Refresh
          </button>
          <button
            onClick={() => {
              clearAdminPassword()
              setStatus('need-auth')
            }}
            className="text-slate-500 hover:underline"
          >
            Sign out
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard label="Page views" value={data.totals.visits} />
        <StatCard label="Unique IPs" value={data.totals.unique_ips} />
        <StatCard label="Analyses" value={data.totals.reports} />
        <StatCard label="Report opens" value={data.totals.report_views} />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Panel title="Top referrers">
          <ul className="space-y-1 text-sm">
            {data.top_referrers.map((r, i) => (
              <li key={i} className="flex justify-between gap-3">
                <span className="truncate text-slate-600">{r.referrer}</span>
                <span className="shrink-0 font-semibold text-slate-800">{r.count}</span>
              </li>
            ))}
          </ul>
        </Panel>

        <Panel title="Most-viewed reports">
          <ul className="space-y-1 text-sm">
            {data.top_reports.map((r) => (
              <li key={r.report_id} className="flex justify-between gap-3">
                <Link to={`/r/${r.report_id}`} className="truncate text-indigo-600 hover:underline">
                  {r.title}
                </Link>
                <span className="shrink-0 font-semibold text-slate-800">{r.view_count}</span>
              </li>
            ))}
          </ul>
        </Panel>

        <Panel title="Top pages">
          <ul className="space-y-1 text-sm">
            {data.top_paths.map((p, i) => (
              <li key={i} className="flex justify-between gap-3">
                <span className="truncate text-slate-600">{p.path}</span>
                <span className="shrink-0 font-semibold text-slate-800">{p.count}</span>
              </li>
            ))}
          </ul>
        </Panel>

        <Panel title="Views by day">
          <ul className="space-y-1 text-sm">
            {data.by_day.map((d, i) => (
              <li key={i} className="flex justify-between gap-3">
                <span className="text-slate-600">{d.day}</span>
                <span className="font-semibold text-slate-800">{d.count}</span>
              </li>
            ))}
          </ul>
        </Panel>
      </div>

      <Panel title={`Recent activity (${data.recent_visits.length})`} className="mt-6">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-slate-400">
              <tr>
                <th className="py-1 pr-3 font-medium">When</th>
                <th className="py-1 pr-3 font-medium">IP</th>
                <th className="py-1 pr-3 font-medium">Path</th>
                <th className="py-1 pr-3 font-medium">Referrer</th>
                <th className="py-1 font-medium">User agent</th>
              </tr>
            </thead>
            <tbody className="text-slate-600">
              {data.recent_visits.map((v, i) => (
                <tr key={i} className="border-t border-slate-100">
                  <td className="whitespace-nowrap py-1 pr-3">{fmtTs(v.ts)}</td>
                  <td className="whitespace-nowrap py-1 pr-3">{v.ip}</td>
                  <td className="py-1 pr-3">{v.path}</td>
                  <td className="max-w-[180px] truncate py-1 pr-3" title={v.referrer ?? ''}>
                    {v.referrer ?? '(direct)'}
                  </td>
                  <td className="max-w-[220px] truncate py-1" title={v.user_agent ?? ''}>
                    {v.user_agent}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  )
}

function Panel({
  title,
  children,
  className = '',
}: {
  title: string
  children: React.ReactNode
  className?: string
}) {
  return (
    <div className={`rounded-2xl border border-slate-200 bg-white p-5 shadow-sm ${className}`}>
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">{title}</h2>
      {children}
    </div>
  )
}
