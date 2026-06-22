/**
 * Diagnostics page — run the v3 pipeline (or load the sample) and inspect every
 * step. The whole point: complete, digestible visibility into the orchestration.
 */

import { useState } from 'react'
import { analyze, getSample, type AnalyzeRequest } from '../lib/api/analyzeApi'
import { handleApiError } from '../lib/api'
import { getPassphrase, setPassphrase } from '../lib/passphrase'
import PassphraseModal from '../components/PassphraseModal'
import DiagnosticsView from '../components/DiagnosticsView'
import type { AnalyzeResult } from '../types/analyze'

type Mode = 'url' | 'text'

export default function DiagnosticsPage() {
  const [mode, setMode] = useState<Mode>('url')
  const [url, setUrl] = useState('')
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<AnalyzeResult | null>(null)

  const [showPass, setShowPass] = useState(false)
  const [passError, setPassError] = useState<string | null>(null)

  function buildRequest(): AnalyzeRequest {
    return mode === 'url' ? { url: url.trim() } : { text: text.trim() }
  }

  async function run() {
    if (mode === 'url' && !url.trim()) return setError('Enter a URL.')
    if (mode === 'text' && !text.trim()) return setError('Paste some article text.')
    if (!getPassphrase()) {
      setPassError(null)
      setShowPass(true)
      return
    }
    setError(null)
    setLoading(true)
    try {
      const res = await analyze(buildRequest())
      setResult(res)
    } catch (e: unknown) {
      const status = (e as { response?: { status?: number } }).response?.status
      if (status === 401) {
        setPassError('That passphrase wasn’t accepted. Try again.')
        setShowPass(true)
      } else {
        setError(handleApiError(e))
      }
    } finally {
      setLoading(false)
    }
  }

  async function loadSample() {
    setError(null)
    setLoading(true)
    try {
      setResult(await getSample())
    } catch (e: unknown) {
      setError(handleApiError(e))
    } finally {
      setLoading(false)
    }
  }

  function onPassphraseSubmit(value: string) {
    setPassphrase(value)
    setShowPass(false)
    setPassError(null)
    run()
  }

  const v = result?.report.verdict

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight text-slate-800">Pipeline diagnostics</h1>
        <p className="mt-1 text-sm text-slate-500">
          Run the analysis and inspect the input and output of every step.
        </p>
      </header>

      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-4 inline-flex rounded-lg bg-slate-100 p-1">
          {(['url', 'text'] as Mode[]).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              disabled={loading}
              className={`rounded-md px-4 py-1.5 text-sm font-medium transition ${mode === m ? 'bg-white text-slate-800 shadow' : 'text-slate-500'}`}
            >
              {m === 'url' ? 'From URL' : 'Paste text'}
            </button>
          ))}
        </div>

        {mode === 'url' ? (
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={loading}
            placeholder="https://…"
            className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          />
        ) : (
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            disabled={loading}
            rows={8}
            placeholder="Paste the full article text here…"
            className="w-full resize-y rounded-lg border border-slate-300 px-3 py-2.5 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          />
        )}

        <div className="mt-4 flex flex-wrap items-center gap-3">
          <button
            onClick={run}
            disabled={loading}
            className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 disabled:opacity-60"
          >
            {loading ? 'Running…' : 'Run analysis'}
          </button>
          <button
            onClick={loadSample}
            disabled={loading}
            className="rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-medium text-slate-600 transition hover:border-slate-400 disabled:opacity-60"
          >
            Load sample
          </button>
          <span className="text-xs text-slate-400">The sample needs no passphrase and spends no tokens.</span>
        </div>

        {error && <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
      </div>

      {v && (
        <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex flex-wrap items-center gap-4">
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-400">Verdict</p>
              <p className="text-lg font-bold text-slate-800">{v.fairness_label}</p>
            </div>
            <div className="ml-auto flex gap-3">
              <Score label="substantive" value={v.substantive_score} />
              <Score label="presentation" value={v.presentation_score} />
              <Score label="overall" value={v.overall_score} accent />
            </div>
          </div>
          <p className="mt-3 text-sm text-slate-600">{v.summary}</p>
          {(v.both_sidesing || v.false_consensus) && (
            <div className="mt-2 flex gap-2">
              {v.both_sidesing && <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-700">both-sidesing</span>}
              {v.false_consensus && <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-700">false consensus</span>}
            </div>
          )}
        </div>
      )}

      {result && (
        <div className="mt-6">
          <DiagnosticsView data={result.diagnostics} />
        </div>
      )}

      {showPass && (
        <PassphraseModal onSubmit={onPassphraseSubmit} onClose={() => setShowPass(false)} error={passError} />
      )}
    </div>
  )
}

function Score({ label, value, accent }: { label: string; value: number; accent?: boolean }) {
  return (
    <div className="min-w-[72px] rounded-lg border border-slate-200 px-3 py-1.5 text-center">
      <p className={`text-xl font-bold leading-none ${accent ? 'text-emerald-600' : 'text-slate-700'}`}>{value}</p>
      <p className="mt-0.5 text-[10px] uppercase tracking-wide text-slate-400">{label}</p>
    </div>
  )
}
