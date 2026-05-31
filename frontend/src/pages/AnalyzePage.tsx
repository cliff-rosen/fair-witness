import { useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { precheckArticle, streamAnalysis } from '../lib/api/analysisApi'
import { clearPassphrase, getPassphrase, setPassphrase } from '../lib/passphrase'
import type { FairnessReport, ReportSummary } from '../types/analysis'
import PipelineProgress, { type Progress } from '../components/PipelineProgress'
import ReportView from '../components/ReportView'
import PassphraseModal from '../components/PassphraseModal'
import ShareBar from '../components/ShareBar'

type Phase = 'idle' | 'running' | 'done' | 'error'
const EMPTY_PROGRESS: Progress = { stages: [], claims: 0, expected: 0 }

type Mode = 'url' | 'text'

const SAMPLE_URL = 'https://apnews.com'

export default function AnalyzePage() {
  const [mode, setMode] = useState<Mode>('url')
  const [url, setUrl] = useState('')
  const [text, setText] = useState('')

  // Optional provenance the user can attach to pasted text.
  const [showMeta, setShowMeta] = useState(false)
  const [meta, setMeta] = useState({
    title: '',
    source_url: '',
    site_name: '',
    byline: '',
    published: '',
    note: '',
  })

  const [phase, setPhase] = useState<Phase>('idle')
  const [error, setError] = useState<string | null>(null)

  // Passphrase is asked at the moment of running (not on landing) and remembered.
  const [showPassModal, setShowPassModal] = useState(false)
  const [passError, setPassError] = useState<string | null>(null)

  // Dedup: if this URL/text was already analyzed, offer it before spending tokens.
  const [existing, setExisting] = useState<ReportSummary | null>(null)
  const [checking, setChecking] = useState(false)

  const [progress, setProgress] = useState<Progress>(EMPTY_PROGRESS)
  const [report, setReport] = useState<FairnessReport | null>(null)

  const cancelRef = useRef<null | (() => void)>(null)

  const running = phase === 'running'

  function reset() {
    setError(null)
    setExisting(null)
    setProgress(EMPTY_PROGRESS)
    setReport(null)
  }

  function buildRequest() {
    if (mode === 'url') return { url: url.trim() }
    const req: Record<string, string> = { text: text.trim() }
    for (const [k, v] of Object.entries(meta)) {
      if (v.trim()) req[k] = v.trim()
    }
    return req
  }

  async function start() {
    setError(null)
    setExisting(null)
    if (mode === 'url' && !url.trim()) {
      setError('Enter a URL.')
      return
    }
    if (mode === 'text' && !text.trim()) {
      setError('Paste some article text.')
      return
    }

    // Dedup check first — cheap, no passphrase, no tokens.
    setChecking(true)
    try {
      const res = await precheckArticle(buildRequest())
      if (res.existing) {
        setExisting(res.existing)
        return
      }
    } catch {
      /* precheck is best-effort — fall through to running */
    } finally {
      setChecking(false)
    }
    proceed()
  }

  /** After validation + dedup: gate on the passphrase, then run. */
  function proceed() {
    if (!getPassphrase()) {
      setPassError(null)
      setShowPassModal(true)
      return
    }
    runAnalysis()
  }

  function analyzeAnyway() {
    setExisting(null)
    proceed()
  }

  function runAnalysis() {
    const request = buildRequest()

    reset()
    setPhase('running')

    cancelRef.current = streamAnalysis(request, {
      onEvent: (event) => {
        const t = event.type
        if (t === 'report') {
          if (event.report) setReport(event.report)
          setPhase('done')
          return
        }
        if (t === 'error') {
          setError(event.message || 'Analysis failed')
          setPhase('error')
          return
        }
        if (t === 'claim_check') {
          setProgress((p) => ({ ...p, claims: p.claims + 1 }))
          return
        }
        if (t === 'argument') {
          const n = event.argument ? Math.min(5, event.argument.claims.length) : 0
          setProgress((p) => ({ ...p, stages: [...p.stages, t], expected: n }))
          return
        }
        // ingested | coherence | rhetoric | structural | reality | omission | verdict
        setProgress((p) => ({ ...p, stages: [...p.stages, t] }))
      },
      onError: (message) => {
        setError(message)
        setPhase('error')
      },
      onAuthError: () => {
        clearPassphrase()
        setPhase('idle')
        setPassError('That passphrase wasn’t accepted. Try again.')
        setShowPassModal(true)
      },
    })
  }

  function onPassphraseSubmit(value: string) {
    setPassphrase(value) // persist so API calls pick it up
    setShowPassModal(false)
    setPassError(null)
    runAnalysis()
  }

  function cancel() {
    cancelRef.current?.()
    setPhase('idle')
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      {/* Input + live orchestration stay comfortably narrow */}
      <div className="mx-auto max-w-3xl">
      <header className="mb-8 text-center">
        <h1 className="text-3xl font-bold tracking-tight text-slate-800">
          Fair&nbsp;Witness
        </h1>
        <p className="mt-1 text-slate-500">
          Orchestrated fairness &amp; bias analysis for any article.
        </p>
      </header>

      {/* Input card */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-4 inline-flex rounded-lg bg-slate-100 p-1">
          {(['url', 'text'] as Mode[]).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              disabled={running}
              className={`rounded-md px-4 py-1.5 text-sm font-medium transition ${
                mode === m ? 'bg-white text-slate-800 shadow' : 'text-slate-500'
              }`}
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
            disabled={running}
            placeholder={`https://...  (e.g. ${SAMPLE_URL}/article)`}
            className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          />
        ) : (
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            disabled={running}
            rows={10}
            placeholder="Paste the full article text here..."
            className="w-full resize-y rounded-lg border border-slate-300 px-3 py-2.5 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          />
        )}

        {mode === 'text' && (
          <div className="mt-3">
            <button
              type="button"
              onClick={() => setShowMeta((s) => !s)}
              className="text-sm font-medium text-indigo-600 hover:text-indigo-700"
            >
              {showMeta ? '− Hide source details' : '+ Add source details (optional)'}
            </button>
            {showMeta && (
              <div className="mt-3 grid gap-3 rounded-lg border border-slate-200 bg-slate-50 p-3 sm:grid-cols-2">
                <Field label="Title" value={meta.title} onChange={(v) => setMeta({ ...meta, title: v })} placeholder="Article headline" />
                <Field label="Original URL" value={meta.source_url} onChange={(v) => setMeta({ ...meta, source_url: v })} placeholder="https://… (e.g. the paywalled page)" />
                <Field label="Publication" value={meta.site_name} onChange={(v) => setMeta({ ...meta, site_name: v })} placeholder="e.g. The New York Times" />
                <Field label="Author" value={meta.byline} onChange={(v) => setMeta({ ...meta, byline: v })} placeholder="Byline" />
                <Field label="Published" value={meta.published} onChange={(v) => setMeta({ ...meta, published: v })} placeholder="e.g. May 20, 2026" />
                <div className="sm:col-span-2">
                  <label className="mb-1 block text-xs font-medium text-slate-500">Note (optional)</label>
                  <textarea
                    value={meta.note}
                    onChange={(e) => setMeta({ ...meta, note: e.target.value })}
                    rows={2}
                    placeholder="Any context for readers — shown on the report, not part of the analysis."
                    className="w-full resize-y rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                  />
                </div>
              </div>
            )}
          </div>
        )}

        <div className="mt-4 flex items-center gap-3">
          {!running ? (
            <button
              onClick={start}
              disabled={checking}
              className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 disabled:opacity-60"
            >
              {checking ? 'Checking…' : 'Analyze'}
            </button>
          ) : (
            <button
              onClick={cancel}
              className="rounded-lg bg-slate-200 px-5 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-300"
            >
              Cancel
            </button>
          )}
          {phase === 'done' && (
            <button
              onClick={() => {
                reset()
                setPhase('idle')
              }}
              className="text-sm text-slate-500 hover:text-slate-700"
            >
              New analysis
            </button>
          )}
        </div>

        {error && (
          <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
        )}

        {existing && (
          <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm">
            <p className="font-semibold text-amber-800">This article was already analyzed.</p>
            <p className="mt-0.5 text-amber-700">
              “{existing.title}” — {existing.fairness_label} ({existing.overall_score}/100).
            </p>
            <div className="mt-2 flex flex-wrap items-center gap-3">
              <Link
                to={`/r/${existing.report_id}`}
                className="rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-semibold text-white transition hover:bg-indigo-700"
              >
                View existing analysis
              </Link>
              <button
                onClick={analyzeAnyway}
                className="text-sm font-medium text-slate-600 hover:text-slate-800"
              >
                Analyze again anyway
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Live progress */}
      {running && (
        <div className="mt-6">
          <PipelineProgress progress={progress} />
        </div>
      )}
      </div>

      {/* Final report — uses the full width */}
      {phase === 'done' && report && (
        <div className="mt-6 space-y-4">
          {report.report_id && <ShareBar reportId={report.report_id} />}
          <ReportView report={report} />
        </div>
      )}

      {showPassModal && (
        <PassphraseModal
          onSubmit={onPassphraseSubmit}
          onClose={() => setShowPassModal(false)}
          error={passError}
        />
      )}
    </div>
  )
}

/** Small labeled text input used in the optional "source details" panel. */
function Field({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string
  value: string
  onChange: (v: string) => void
  placeholder?: string
}) {
  return (
    <div>
      <label className="mb-1 block text-xs font-medium text-slate-500">{label}</label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
      />
    </div>
  )
}

