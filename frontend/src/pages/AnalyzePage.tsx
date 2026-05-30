import { useRef, useState } from 'react'
import { streamAnalysis } from '../lib/api/analysisApi'
import type {
  AnalysisPlan,
  BiasReport,
  ClaimAssessment,
  DimensionAssessment,
  ExtractedArticle,
  IssueMap,
  PlannedDimension,
} from '../types/analysis'
import OrchestrationProgress, { type Phase } from '../components/OrchestrationProgress'
import ReportView from '../components/ReportView'
import MethodologyModal from '../components/MethodologyModal'

type Mode = 'url' | 'text'

const SAMPLE_URL = 'https://apnews.com'

export default function AnalyzePage() {
  const [mode, setMode] = useState<Mode>('url')
  const [url, setUrl] = useState('')
  const [text, setText] = useState('')

  const [phase, setPhase] = useState<Phase>('idle')
  const [error, setError] = useState<string | null>(null)
  const [showMethodology, setShowMethodology] = useState(false)

  const [article, setArticle] = useState<ExtractedArticle | null>(null)
  const [plan, setPlan] = useState<AnalysisPlan | null>(null)
  const [issueMap, setIssueMap] = useState<IssueMap | null>(null)
  const [plannedDims, setPlannedDims] = useState<PlannedDimension[]>([])
  const [completed, setCompleted] = useState<Map<string, DimensionAssessment>>(new Map())
  const [claims, setClaims] = useState<ClaimAssessment[] | null>(null)
  const [report, setReport] = useState<BiasReport | null>(null)

  const cancelRef = useRef<null | (() => void)>(null)

  const running = phase !== 'idle' && phase !== 'done' && phase !== 'error'

  function reset() {
    setError(null)
    setArticle(null)
    setPlan(null)
    setIssueMap(null)
    setPlannedDims([])
    setCompleted(new Map())
    setClaims(null)
    setReport(null)
  }

  function start() {
    const request = mode === 'url' ? { url: url.trim() } : { text: text.trim() }
    if (mode === 'url' && !request.url) {
      setError('Enter a URL.')
      return
    }
    if (mode === 'text' && !request.text) {
      setError('Paste some article text.')
      return
    }

    reset()
    setPhase('ingesting')

    cancelRef.current = streamAnalysis(request, {
      onEvent: (event) => {
        switch (event.type) {
          case 'ingested':
            if (event.article) setArticle(event.article)
            setPhase('planning')
            break
          case 'plan':
            if (event.plan) setPlan(event.plan)
            setPhase('mapping')
            break
          case 'issue_map':
            if (event.issue_map) setIssueMap(event.issue_map)
            break
          case 'dimensions_planned':
            if (event.dimensions) setPlannedDims(event.dimensions)
            setPhase('evaluating')
            break
          case 'dimension_complete':
            if (event.assessment) {
              setCompleted((prev) => {
                const next = new Map(prev)
                next.set(event.assessment!.key, event.assessment!)
                return next
              })
            }
            break
          case 'claims_analyzed':
            setClaims(event.claims ?? [])
            break
          case 'synthesizing':
            setPhase('synthesizing')
            break
          case 'report':
            if (event.report) setReport(event.report)
            setPhase('done')
            break
          case 'error':
            setError(event.message || 'Analysis failed')
            setPhase('error')
            break
        }
      },
      onError: (message) => {
        setError(message)
        setPhase('error')
      },
    })
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
        <button
          onClick={() => setShowMethodology(true)}
          className="mt-3 inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1 text-sm font-medium text-slate-600 shadow-sm transition hover:border-indigo-200 hover:text-indigo-600"
        >
          <span aria-hidden>ⓘ</span> How it works
        </button>
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

        <div className="mt-4 flex items-center gap-3">
          {!running ? (
            <button
              onClick={start}
              className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700"
            >
              Analyze
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
      </div>

      {/* Live orchestration */}
      {phase !== 'idle' && phase !== 'done' && (
        <div className="mt-6">
          <OrchestrationProgress
            phase={phase}
            article={article}
            plan={plan}
            issueMap={issueMap}
            plannedDims={plannedDims}
            completedKeys={new Set(completed.keys())}
            claimsDone={claims !== null}
          />
        </div>
      )}
      </div>

      {/* Final report — uses the full width */}
      {phase === 'done' && report && (
        <div className="mt-6">
          <ReportView report={report} />
        </div>
      )}

      {showMethodology && <MethodologyModal onClose={() => setShowMethodology(false)} />}
    </div>
  )
}
