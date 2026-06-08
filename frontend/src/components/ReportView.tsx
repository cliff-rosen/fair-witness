import type {
  ArgClaim,
  ArgumentMap,
  ClaimCheck,
  Evidence,
  FairnessReport,
  OmissionAssessment,
  RealityModel,
  Ring0Result,
  WebStep,
} from '../types/analysis'
import { leanLabel, scoreColor, scoreTrackColor, severityBadge } from '../lib/ui'
import ScoreGauge from './ScoreGauge'
import Tabs, { type TabDef } from './Tabs'

// ---------------------------------------------------------------------------
// small shared bits
// ---------------------------------------------------------------------------

function fmtDate(iso?: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  return isNaN(d.getTime()) ? iso : d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}
function domainOf(url: string): string {
  try {
    const h = new URL(url).hostname.toLowerCase()
    return h.startsWith('www.') ? h.slice(4) : h
  } catch {
    return url
  }
}
function Pill({ children, cls = 'bg-slate-100 text-slate-600' }: { children: React.ReactNode; cls?: string }) {
  return <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${cls}`}>{children}</span>
}

/** A short plain-English note explaining what a section is. */
function Signpost({ children }: { children: React.ReactNode }) {
  return <p className="mb-4 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-500">{children}</p>
}

const VERDICT_META: Record<string, { label: string; cls: string }> = {
  supported: { label: 'Supported', cls: 'bg-green-100 text-green-800' },
  mostly_supported: { label: 'Mostly supported', cls: 'bg-lime-100 text-lime-800' },
  mixed: { label: 'Mixed', cls: 'bg-amber-100 text-amber-800' },
  contradicted: { label: 'Contradicted', cls: 'bg-red-100 text-red-800' },
  unsupported: { label: 'Unsupported', cls: 'bg-orange-100 text-orange-800' },
  unverifiable: { label: "Couldn't verify", cls: 'bg-slate-100 text-slate-600' },
}
const PRESENTED: Record<string, string> = {
  asserted: 'stated as fact',
  attributed: 'attributed to a source',
  hedged: 'hedged',
}

function TraceList({ trace }: { trace: WebStep[] }) {
  if (!trace?.length) return null
  return (
    <details className="mt-2 text-xs text-slate-500">
      <summary className="cursor-pointer font-medium text-slate-500">What we searched &amp; read ({trace.length})</summary>
      <ul className="mt-1 space-y-0.5">
        {trace.map((s, i) => (
          <li key={i} className="truncate">
            {s.kind === 'search' ? `searched: “${s.query}” (${s.result_count ?? 0} results)` : `read: ${s.title || s.url}`}
          </li>
        ))}
      </ul>
    </details>
  )
}

/** One evidence quote with its source + an honest confirmation chip. */
function EvidenceItem({ e }: { e: Evidence }) {
  return (
    <div className="rounded-lg bg-slate-50 p-2.5 text-xs">
      <p className="border-l-2 border-slate-300 pl-2 italic text-slate-600">“{e.quote}”</p>
      <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1">
        <span className="text-slate-500">{e.stance}</span>
        <span className="text-slate-300">·</span>
        <a href={e.source_url} target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline">
          {domainOf(e.source_url)} ↗
        </a>
        <span className="text-slate-300">·</span>
        <span
          className={e.verified ? 'text-green-700' : 'text-amber-700'}
          title={
            e.verified
              ? 'We re-found this exact quote on the cited page (it is a real quote, not fabricated).'
              : "We could not re-find this quote in the pages we read — treat it with caution."
          }
        >
          {e.verified ? '✓ quote confirmed on the page' : '⚠ quote not confirmed'}
        </span>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// source bar (provenance of the article itself)
// ---------------------------------------------------------------------------

function NoteLine({ note }: { note: string }) {
  return (
    <p className="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">
      <span className="font-semibold">Submitter’s note:</span> {note}
    </p>
  )
}

function SourceBar({ report }: { report: FairnessReport }) {
  const { article, created_at } = report
  const analyzed = fmtDate(created_at)
  const words = `${article.word_count.toLocaleString()} words${article.truncated ? ' (truncated)' : ''}`
  if (!article.source_url) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex items-center gap-2 text-sm">
          <span aria-hidden>📋</span>
          <span className="font-semibold text-slate-700">Pasted text</span>
          <span className="text-slate-400">— no original source URL</span>
        </div>
        <p className="mt-1 text-xs text-slate-400">
          {article.byline ? `By ${article.byline} · ` : ''}{analyzed ? `Analyzed ${analyzed} · ` : ''}{words}
        </p>
        {article.note && <NoteLine note={article.note} />}
      </div>
    )
  }
  const publication = article.site_name || domainOf(article.source_url)
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-x-2 text-sm">
            <span aria-hidden>🌐</span>
            <span className="font-semibold text-slate-800">{publication}</span>
            {article.byline && <span className="text-slate-500">· By {article.byline}</span>}
            {article.published && <span className="text-slate-500">· {fmtDate(article.published)}</span>}
          </div>
          <a href={article.source_url} target="_blank" rel="noreferrer" className="mt-0.5 block truncate text-xs text-indigo-600 hover:underline" title={article.source_url}>
            {article.source_url}
          </a>
          <p className="mt-1 text-xs text-slate-400">{analyzed ? `Analyzed ${analyzed} · ` : ''}{words}</p>
        </div>
        <a href={article.source_url} target="_blank" rel="noreferrer" className="shrink-0 rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-2 text-sm font-semibold text-indigo-700 transition hover:bg-indigo-100">
          Read the original ↗
        </a>
      </div>
      {article.note && <NoteLine note={article.note} />}
    </div>
  )
}

// ---------------------------------------------------------------------------
// TAB 1 — Reasoning & tone  (the text-only assessment)
// ---------------------------------------------------------------------------

function ScoreHeader({ label, score }: { label: string; score: number }) {
  return (
    <div className="mb-2 flex items-center gap-3">
      <div className="flex h-9 w-9 items-center justify-center rounded-full text-sm font-bold text-white" style={{ background: scoreColor(score) }}>{score}</div>
      <h3 className="font-semibold text-slate-800">{label}</h3>
    </div>
  )
}

function ReasoningTab({ ring0 }: { ring0: Ring0Result }) {
  const { coherence: c, rhetoric: r, structural: s } = ring0
  return (
    <div className="space-y-3">
      <Signpost>
        Judged from the article’s text alone — no outside facts. This is about whether it’s <b>well-made</b>:
        does the argument hold together, and is the language fair for its genre?
      </Signpost>

      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <ScoreHeader label="Does the argument hold together?" score={c.score} />
        <div className="mb-2 flex flex-wrap gap-1.5 text-xs">
          <Pill cls={c.thesis_follows ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>{c.thesis_follows ? 'conclusion follows from its claims' : 'conclusion does not follow'}</Pill>
        </div>
        <p className="text-sm text-slate-700">{c.rationale}</p>
        {c.issues.length > 0 && (
          <ul className="mt-2 space-y-1 text-sm">
            {c.issues.map((i, k) => (
              <li key={k} className="rounded-lg bg-red-50 px-3 py-1.5 text-red-900">
                <span className="font-semibold">{i.kind.replace(/_/g, ' ')}</span>: {i.detail}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <ScoreHeader label={`Is the language fair? — tone: ${r.tone}`} score={r.score} />
        <p className="text-sm text-slate-700">{r.rationale}</p>
        {r.findings.length > 0 && (
          <div className="mt-2 space-y-2">
            {r.findings.map((f, k) => (
              <div key={k} className="rounded-lg bg-slate-50 p-3">
                <Pill cls={severityBadge(f.severity)}>{f.severity}</Pill>
                <p className="mt-1 border-l-2 border-slate-300 pl-2 text-sm italic text-slate-700">“{f.quote}”</p>
                <p className="mt-1 text-xs text-slate-500">{f.issue}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <ScoreHeader label="Is it internally consistent?" score={s.score} />
        <div className="mb-2 flex flex-wrap gap-1.5 text-xs">
          <Pill cls={s.headline_matches_body ? 'bg-green-100 text-green-800' : 'bg-amber-100 text-amber-800'}>headline {s.headline_matches_body ? 'matches the body' : 'overreaches'}</Pill>
          <Pill cls={s.opinion_fact_separation ? 'bg-green-100 text-green-800' : 'bg-amber-100 text-amber-800'}>opinion {s.opinion_fact_separation ? 'kept separate from fact' : 'blended with fact'}</Pill>
        </div>
        {s.headline_note && <p className="text-sm text-slate-600">{s.headline_note}</p>}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// TAB 2 — Fact-check  (the web-grounded assessment + the drill-down)
// ---------------------------------------------------------------------------

function ClaimCard({ cc, claim }: { cc: ClaimCheck; claim?: ArgClaim }) {
  const v = VERDICT_META[cc.verdict] || { label: cc.verdict, cls: 'bg-slate-100 text-slate-600' }
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      {/* 1 — what the article claims */}
      <div className="text-xs font-semibold uppercase tracking-wide text-slate-400">
        The article claims {claim ? <span className="font-normal lowercase">· {PRESENTED[claim.as_presented]}</span> : null}
      </div>
      <p className="mt-0.5 text-sm font-medium text-slate-800">“{cc.claim}”</p>

      {/* 2 — our check */}
      <div className="mt-3 flex items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">Our check</span>
        <Pill cls={v.cls}>{v.label}</Pill>
      </div>
      <p className="mt-1 text-sm text-slate-600">{cc.finding}</p>

      {/* 3 — the evidence */}
      {cc.evidence.length > 0 && (
        <div className="mt-3">
          <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">Evidence</div>
          <div className="space-y-1.5">
            {cc.evidence.map((e, i) => <EvidenceItem key={i} e={e} />)}
          </div>
        </div>
      )}
      <TraceList trace={cc.trace} />
    </div>
  )
}

function FactCheckTab({
  reality,
  claim_checks,
  omission,
  argument,
}: {
  reality: RealityModel
  claim_checks: ClaimCheck[]
  omission: OmissionAssessment
  argument: ArgumentMap
}) {
  const byId = new Map(argument.claims.map((c) => [c.id, c]))
  return (
    <div className="space-y-4">
      <Signpost>
        We searched the live web to check the article’s most load-bearing claims and what it leaves out.
        <b> “Our check”</b> is our judgment of whether each claim holds up. On each quote, <b>“✓ quote confirmed”</b> means
        we re-found that exact text on the cited page — it confirms the <i>quote is real</i>, not that the claim is true.
      </Signpost>

      {/* the claim-by-claim drill-down */}
      <div className="space-y-2">
        {claim_checks.map((cc, i) => (
          <ClaimCard key={i} cc={cc} claim={byId.get(cc.claim_id)} />
        ))}
      </div>

      {/* what it leaves out */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <ScoreHeader label="What it leaves out" score={omission.score} />
        <div className="mb-2 flex flex-wrap gap-1.5 text-xs">
          {omission.adopted_framing && <Pill>adopts framing: {omission.adopted_framing}</Pill>}
          {omission.both_sidesing && <Pill cls="bg-amber-100 text-amber-800">⚠ both-sides a settled issue</Pill>}
          {omission.false_consensus && <Pill cls="bg-amber-100 text-amber-800">⚠ presents the contested as settled</Pill>}
        </div>
        {omission.omissions.length > 0 && (
          <ul className="space-y-1.5 text-sm">
            {omission.omissions.map((o, i) => (
              <li key={i} className="rounded-lg bg-slate-50 px-3 py-2">
                <Pill cls={severityBadge(o.severity)}>{o.severity}</Pill>{' '}
                <span className="font-medium text-slate-700">{o.missing}</span>
                <span className="text-slate-500"> — {o.why_it_matters}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* the reference map we checked against (collapsed — supporting detail) */}
      <details className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <summary className="cursor-pointer text-sm font-semibold text-slate-700">
          The reference picture we checked against (what the web says about this topic)
        </summary>
        <p className="mt-2 text-sm text-slate-600">{reality.structure_note}</p>
        {reality.key_facts.length > 0 && (
          <div className="mt-2 space-y-1.5">
            {reality.key_facts.map((f, i) => (
              <div key={i} className="text-sm">
                <span className="mr-2 rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-500">{f.status}</span>
                <span className="text-slate-700">{f.fact}</span>
              </div>
            ))}
          </div>
        )}
      </details>
    </div>
  )
}

// ---------------------------------------------------------------------------
// TAB 3 — The article (raw material)
// ---------------------------------------------------------------------------

function ArticleTab({ argument, text, truncated, words }: { argument: ArgumentMap; text: string; truncated: boolean; words: number }) {
  const claims = [...argument.claims].sort((a, b) => b.load_bearing - a.load_bearing)
  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <Signpost>How we read the article’s argument: its main point, and the claims holding it up. The bigger the number, the more the argument depends on that claim.</Signpost>
        <h3 className="mb-1 text-sm font-semibold uppercase tracking-wide text-slate-400">Main point</h3>
        <p className="text-sm text-slate-700">{argument.thesis}</p>
        <div className="mt-3 space-y-1.5">
          {claims.map((c) => (
            <div key={c.id} className="flex items-start gap-3">
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[11px] font-bold text-white" style={{ background: scoreColor(c.load_bearing) }} title="how load-bearing">{c.load_bearing}</div>
              <p className="text-sm text-slate-700">{c.text} <span className="text-slate-400">({PRESENTED[c.as_presented]})</span></p>
            </div>
          ))}
        </div>
      </div>
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-400">The exact text we analyzed</h3>
        {truncated && <p className="mb-2 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">Truncated to fit the model — analysis saw the first {words.toLocaleString()} words.</p>}
        <div className="max-h-[28rem] overflow-y-auto whitespace-pre-wrap rounded-lg bg-slate-50 p-3 text-sm leading-relaxed text-slate-700">{text}</div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------

export default function ReportView({ report }: { report: FairnessReport }) {
  const { article, argument, ring0, ring1, verdict } = report

  const tabs: TabDef[] = [
    { id: 'reasoning', label: 'Reasoning & tone', content: <ReasoningTab ring0={ring0} /> },
    {
      id: 'factcheck',
      label: 'Fact-check',
      count: ring1.claim_checks.length,
      content: <FactCheckTab reality={ring1.reality} claim_checks={ring1.claim_checks} omission={ring1.omission} argument={argument} />,
    },
    {
      id: 'article',
      label: 'The article',
      content: <ArticleTab argument={argument} text={article.text} truncated={article.truncated} words={article.word_count} />,
    },
  ]

  return (
    <div className="animate-fade-in space-y-6">
      <SourceBar report={report} />

      {/* verdict */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col items-center gap-6 md:flex-row md:items-start">
          <ScoreGauge score={verdict.overall_score} label={verdict.fairness_label} />
          <div className="flex-1">
            <h2 className="text-lg font-bold text-slate-800">{article.title}</h2>
            <div className="mt-2 flex flex-wrap gap-2 text-xs">
              <Pill>{argument.genre}</Pill>
              <Pill>Leans {leanLabel(verdict.political_lean)} ({verdict.lean_confidence}% sure)</Pill>
            </div>

            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <div>
                <div className="flex items-baseline justify-between">
                  <span className="text-sm font-medium text-slate-700">Reasoning</span>
                  <span className="text-sm font-bold" style={{ color: scoreColor(verdict.coherence_score) }}>{verdict.coherence_score}</span>
                </div>
                <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-slate-100"><div className={`h-full rounded-full ${scoreTrackColor(verdict.coherence_score)}`} style={{ width: `${verdict.coherence_score}%` }} /></div>
                <p className="mt-1 text-xs text-slate-400">Does the argument hold together? (from the text)</p>
              </div>
              <div>
                <div className="flex items-baseline justify-between">
                  <span className="text-sm font-medium text-slate-700">Accuracy</span>
                  <span className="text-sm font-bold" style={{ color: scoreColor(verdict.correspondence_score) }}>{verdict.correspondence_score}</span>
                </div>
                <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-slate-100"><div className={`h-full rounded-full ${scoreTrackColor(verdict.correspondence_score)}`} style={{ width: `${verdict.correspondence_score}%` }} /></div>
                <p className="mt-1 text-xs text-slate-400">Do its facts check out, and what’s missing? (web-checked)</p>
              </div>
            </div>

            <p className="mt-4 text-sm leading-relaxed text-slate-700">{verdict.executive_summary}</p>
          </div>
        </div>

        {(verdict.key_strengths.length > 0 || verdict.key_concerns.length > 0) && (
          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <div className="rounded-xl bg-green-50 p-4">
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-green-700">What it does well</h4>
              <ul className="list-inside list-disc space-y-1 text-sm text-green-900">{verdict.key_strengths.map((s, i) => <li key={i}>{s}</li>)}</ul>
            </div>
            <div className="rounded-xl bg-red-50 p-4">
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-red-700">Where it falls short</h4>
              <ul className="list-inside list-disc space-y-1 text-sm text-red-900">{verdict.key_concerns.map((s, i) => <li key={i}>{s}</li>)}</ul>
            </div>
          </div>
        )}
      </div>

      <Tabs tabs={tabs} initialId="factcheck" />
    </div>
  )
}
