import type {
  ArgumentMap,
  ClaimCheck,
  Evidence,
  FairnessReport,
  RealityModel,
  Ring0Result,
  WebStep,
} from '../types/analysis'
import { leanLabel, scoreColor, scoreTrackColor, severityBadge, structureLabel } from '../lib/ui'
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

function AxisBar({ label, score, hint }: { label: string; score: number; hint: string }) {
  return (
    <div>
      <div className="flex items-baseline justify-between">
        <span className="text-sm font-medium text-slate-700">{label}</span>
        <span className="text-sm font-bold" style={{ color: scoreColor(score) }}>{score}</span>
      </div>
      <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-slate-100">
        <div className={`h-full rounded-full ${scoreTrackColor(score)}`} style={{ width: `${score}%`, transition: 'width .6s ease' }} />
      </div>
      <p className="mt-1 text-xs text-slate-400">{hint}</p>
    </div>
  )
}

const VERDICT_CLS: Record<string, string> = {
  supported: 'bg-green-100 text-green-800',
  mostly_supported: 'bg-lime-100 text-lime-800',
  mixed: 'bg-amber-100 text-amber-800',
  contradicted: 'bg-red-100 text-red-800',
  unsupported: 'bg-orange-100 text-orange-800',
  unverifiable: 'bg-slate-100 text-slate-600',
}

function Pill({ children, cls = 'bg-slate-100 text-slate-600' }: { children: React.ReactNode; cls?: string }) {
  return <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${cls}`}>{children}</span>
}

function EvidenceList({ items }: { items: Evidence[] }) {
  if (!items?.length) return null
  return (
    <div className="mt-2 space-y-1.5">
      {items.map((e, i) => (
        <div key={i} className="rounded-lg bg-slate-50 p-2 text-xs">
          <div className="mb-0.5 flex items-center gap-2">
            <span className={e.verified ? 'font-semibold text-green-700' : 'font-semibold text-amber-700'}>
              {e.verified ? '✓ verified' : '⚠ unverified'}
            </span>
            <span className="text-slate-400">·</span>
            <span className="text-slate-500">{e.stance}</span>
            <a href={e.source_url} target="_blank" rel="noreferrer" className="ml-auto truncate text-indigo-600 hover:underline">
              {domainOf(e.source_url)} ↗
            </a>
          </div>
          <p className="border-l-2 border-slate-300 pl-2 italic text-slate-600">“{e.quote}”</p>
        </div>
      ))}
    </div>
  )
}

function TraceList({ trace }: { trace: WebStep[] }) {
  if (!trace?.length) return null
  return (
    <details className="mt-2 text-xs text-slate-500">
      <summary className="cursor-pointer font-medium text-slate-500">Search trace ({trace.length})</summary>
      <ul className="mt-1 space-y-0.5">
        {trace.map((s, i) => (
          <li key={i} className="truncate">
            {s.kind === 'search' ? `🔎 ${s.query} (${s.result_count ?? 0})` : `📄 ${s.title || s.url}`}
          </li>
        ))}
      </ul>
    </details>
  )
}

// ---------------------------------------------------------------------------
// source bar
// ---------------------------------------------------------------------------

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
function NoteLine({ note }: { note: string }) {
  return (
    <p className="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">
      <span className="font-semibold">Submitter’s note:</span> {note}
    </p>
  )
}

// ---------------------------------------------------------------------------
// tab content
// ---------------------------------------------------------------------------

function ArgumentView({ am }: { am: ArgumentMap }) {
  const claims = [...am.claims].sort((a, b) => b.load_bearing - a.load_bearing)
  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="mb-1 text-sm font-semibold uppercase tracking-wide text-slate-400">Thesis</h3>
        <p className="text-sm text-slate-700">{am.thesis}</p>
        <p className="mt-2 text-xs text-slate-400">The higher a claim's load-bearing score, the more the thesis depends on it (and the more it's worth reality-checking).</p>
      </div>
      <div className="space-y-2">
        {claims.map((c) => (
          <div key={c.id} className="flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white" style={{ background: scoreColor(c.load_bearing) }} title="load-bearing">
              {c.load_bearing}
            </div>
            <div className="min-w-0">
              <p className="text-sm text-slate-800">{c.text}</p>
              <div className="mt-1 flex flex-wrap gap-1.5">
                <Pill>{c.kind}</Pill>
                <Pill>{c.as_presented}</Pill>
                {c.supports?.length > 0 && <Pill>supports: {c.supports.join(', ')}</Pill>}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function ScoreHeader({ label, score }: { label: string; score: number }) {
  return (
    <div className="mb-2 flex items-center gap-3">
      <div className="flex h-9 w-9 items-center justify-center rounded-full text-sm font-bold text-white" style={{ background: scoreColor(score) }}>{score}</div>
      <h3 className="font-semibold text-slate-800">{label}</h3>
    </div>
  )
}

function Ring0View({ ring0 }: { ring0: Ring0Result }) {
  const { coherence: c, rhetoric: r, structural: s } = ring0
  return (
    <div className="space-y-3">
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <ScoreHeader label="Logic & coherence" score={c.score} />
        <div className="mb-2 flex flex-wrap gap-1.5 text-xs">
          <Pill cls={c.thesis_follows ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>thesis {c.thesis_follows ? 'follows' : 'does not follow'}</Pill>
          <Pill cls={c.closes_loop ? 'bg-green-100 text-green-800' : 'bg-amber-100 text-amber-800'}>{c.closes_loop ? 'closes the loop' : 'leaves loose ends'}</Pill>
        </div>
        <p className="text-sm text-slate-700">{c.rationale}</p>
        {c.issues.length > 0 && (
          <ul className="mt-2 space-y-1 text-sm">
            {c.issues.map((i, k) => (
              <li key={k} className="rounded-lg bg-red-50 px-3 py-1.5 text-red-900">
                <span className="font-semibold">{i.kind.replace(/_/g, ' ')}</span>
                {i.claim_ids.length > 0 && <span className="text-red-500"> ({i.claim_ids.join(', ')})</span>}: {i.detail}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <ScoreHeader label={`Rhetoric & tone — ${r.tone}`} score={r.score} />
        <p className="text-sm text-slate-700">{r.rationale}</p>
        {r.findings.length > 0 && (
          <div className="mt-2 space-y-2">
            {r.findings.map((f, k) => (
              <div key={k} className="rounded-lg bg-slate-50 p-3">
                <div className="flex items-center gap-2">
                  <Pill cls={severityBadge(f.severity)}>{f.severity}</Pill>
                </div>
                <p className="mt-1 border-l-2 border-slate-300 pl-2 text-sm italic text-slate-700">“{f.quote}”</p>
                <p className="mt-1 text-xs text-slate-500">{f.issue}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <ScoreHeader label="Structural self-consistency" score={s.score} />
        <div className="mb-2 flex flex-wrap gap-1.5 text-xs">
          <Pill cls={s.headline_matches_body ? 'bg-green-100 text-green-800' : 'bg-amber-100 text-amber-800'}>headline {s.headline_matches_body ? 'matches body' : 'overreaches'}</Pill>
          <Pill cls={s.contested_claims_attributed ? 'bg-green-100 text-green-800' : 'bg-amber-100 text-amber-800'}>claims {s.contested_claims_attributed ? 'attributed' : 'asserted'}</Pill>
          <Pill cls={s.opinion_fact_separation ? 'bg-green-100 text-green-800' : 'bg-amber-100 text-amber-800'}>opinion {s.opinion_fact_separation ? 'separated' : 'blended'}</Pill>
        </div>
        {s.headline_note && <p className="text-sm text-slate-600">{s.headline_note}</p>}
        {s.findings.length > 0 && (
          <ul className="mt-2 list-inside list-disc space-y-0.5 text-sm text-slate-600">
            {s.findings.map((f, k) => <li key={k}>{f}</li>)}
          </ul>
        )}
      </div>
    </div>
  )
}

function ClaimCheckCard({ cc }: { cc: ClaimCheck }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-sm font-medium text-slate-800">“{cc.claim}”</p>
      <div className="mt-2 flex flex-wrap items-center gap-1.5">
        <Pill cls={VERDICT_CLS[cc.verdict] || 'bg-slate-100 text-slate-600'}>{cc.verdict.replace(/_/g, ' ')}</Pill>
        <Pill>{cc.handling.replace(/_/g, ' ')}</Pill>
      </div>
      <p className="mt-2 text-sm text-slate-600">{cc.finding}</p>
      <EvidenceList items={cc.evidence} />
      <TraceList trace={cc.trace} />
    </div>
  )
}

function Ring1View({ reality, claim_checks, omission }: { reality: RealityModel; claim_checks: ClaimCheck[]; omission: any }) {
  return (
    <div className="space-y-4">
      {/* reality model */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-1 flex items-center gap-2">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Grounded reality map</h3>
          <Pill cls="bg-indigo-50 text-indigo-700">{structureLabel(reality.structure)}</Pill>
        </div>
        <p className="mb-3 text-sm text-slate-600">{reality.structure_note}</p>
        {reality.key_facts.length > 0 && (
          <div className="space-y-1.5">
            {reality.key_facts.map((f, i) => (
              <div key={i} className="text-sm">
                <span className="mr-2 rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-500">{f.status}</span>
                <span className="text-slate-700">{f.fact}</span>
                <EvidenceList items={f.evidence} />
              </div>
            ))}
          </div>
        )}
        {reality.common_distortions.length > 0 && (
          <p className="mt-3 text-xs text-slate-400"><span className="font-semibold">Common distortions:</span> {reality.common_distortions.join('; ')}</p>
        )}
        <TraceList trace={reality.trace} />
      </div>

      {/* claim checks */}
      <div>
        <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-400">Claim checks ({claim_checks.length})</h3>
        <div className="space-y-2">
          {claim_checks.map((cc, i) => <ClaimCheckCard key={i} cc={cc} />)}
        </div>
      </div>

      {/* omission */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <ScoreHeader label="Omission & framing" score={omission.score} />
        <div className="mb-2 flex flex-wrap gap-1.5 text-xs">
          {omission.adopted_framing && <Pill>framing: {omission.adopted_framing}</Pill>}
          {omission.both_sidesing && <Pill cls="bg-amber-100 text-amber-800">⚠ both-sides a settled issue</Pill>}
          {omission.false_consensus && <Pill cls="bg-amber-100 text-amber-800">⚠ contested-as-settled</Pill>}
        </div>
        {omission.omissions.length > 0 && (
          <ul className="space-y-1.5 text-sm">
            {omission.omissions.map((o: any, i: number) => (
              <li key={i} className="rounded-lg bg-slate-50 px-3 py-2">
                <Pill cls={severityBadge(o.severity)}>{o.severity}</Pill>{' '}
                <span className="font-medium text-slate-700">{o.missing}</span>
                <span className="text-slate-500"> — {o.why_it_matters}</span>
              </li>
            ))}
          </ul>
        )}
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
    {
      id: 'argument',
      label: 'The argument',
      content: <ArgumentView am={argument} />,
    },
    {
      id: 'coherence',
      label: 'Coherence & style',
      content: <Ring0View ring0={ring0} />,
    },
    {
      id: 'reality',
      label: 'Reality check',
      count: ring1.claim_checks.length,
      content: <Ring1View reality={ring1.reality} claim_checks={ring1.claim_checks} omission={ring1.omission} />,
    },
    {
      id: 'text',
      label: 'Source text',
      content: (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-400">The exact text we analyzed</h3>
          {article.truncated && (
            <p className="mb-2 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">
              Truncated to fit the model budget — analysis saw the first {article.word_count.toLocaleString()} words.
            </p>
          )}
          <div className="max-h-[28rem] overflow-y-auto whitespace-pre-wrap rounded-lg bg-slate-50 p-3 text-sm leading-relaxed text-slate-700">{article.text}</div>
        </div>
      ),
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
              <Pill>Lean: {leanLabel(verdict.political_lean)} ({verdict.lean_confidence}%)</Pill>
              {verdict.both_sidesing && <Pill cls="bg-amber-100 text-amber-800">⚠ both-sidesing</Pill>}
              {verdict.false_consensus && <Pill cls="bg-amber-100 text-amber-800">⚠ false consensus</Pill>}
            </div>

            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <AxisBar label="Coherence" score={verdict.coherence_score} hint="Internal — does the reasoning hold together (read from the text)" />
              <AxisBar label="Correspondence" score={verdict.correspondence_score} hint="External — does it hold up vs reality (web-checked)" />
            </div>

            <p className="mt-4 text-sm leading-relaxed text-slate-700">{verdict.executive_summary}</p>
          </div>
        </div>

        {(verdict.key_strengths.length > 0 || verdict.key_concerns.length > 0) && (
          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <div className="rounded-xl bg-green-50 p-4">
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-green-700">Strengths</h4>
              <ul className="list-inside list-disc space-y-1 text-sm text-green-900">
                {verdict.key_strengths.map((s, i) => <li key={i}>{s}</li>)}
              </ul>
            </div>
            <div className="rounded-xl bg-red-50 p-4">
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-red-700">Concerns</h4>
              <ul className="list-inside list-disc space-y-1 text-sm text-red-900">
                {verdict.key_concerns.map((s, i) => <li key={i}>{s}</li>)}
              </ul>
            </div>
          </div>
        )}
      </div>

      <Tabs tabs={tabs} initialId="argument" />
    </div>
  )
}
