import type { BiasReport } from '../types/analysis'
import { leanLabel, scoreColor, scoreTrackColor } from '../lib/ui'
import ScoreGauge from './ScoreGauge'
import DimensionCard from './DimensionCard'
import IssueMapView from './IssueMapView'
import ClaimsView from './ClaimsView'
import Tabs, { type TabDef } from './Tabs'

function AxisBar({ label, score, hint }: { label: string; score: number; hint: string }) {
  return (
    <div>
      <div className="flex items-baseline justify-between">
        <span className="text-sm font-medium text-slate-700">{label}</span>
        <span className="text-sm font-bold" style={{ color: scoreColor(score) }}>
          {score}
        </span>
      </div>
      <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className={`h-full rounded-full ${scoreTrackColor(score)}`}
          style={{ width: `${score}%`, transition: 'width 0.6s ease' }}
        />
      </div>
      <p className="mt-1 text-xs text-slate-400">{hint}</p>
    </div>
  )
}

function fmtDate(iso?: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso // show the raw string if it isn't ISO
  return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

function domainOf(url: string): string {
  try {
    const h = new URL(url).hostname.toLowerCase()
    return h.startsWith('www.') ? h.slice(4) : h
  } catch {
    return url
  }
}

/** Prominent provenance bar: where this article came from. */
function SourceBar({ report }: { report: BiasReport }) {
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
          {article.byline ? `By ${article.byline} · ` : ''}
          {analyzed ? `Analyzed ${analyzed} · ` : ''}
          {words}
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
          <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-sm">
            <span aria-hidden>🌐</span>
            <span className="font-semibold text-slate-800">{publication}</span>
            {article.byline && <span className="text-slate-500">· By {article.byline}</span>}
            {article.published && (
              <span className="text-slate-500">· {fmtDate(article.published)}</span>
            )}
          </div>
          <a
            href={article.source_url}
            target="_blank"
            rel="noreferrer"
            className="mt-0.5 block truncate text-xs text-indigo-600 hover:underline"
            title={article.source_url}
          >
            {article.source_url}
          </a>
          <p className="mt-1 text-xs text-slate-400">
            {analyzed ? `Analyzed ${analyzed} · ` : ''}
            {words}
          </p>
        </div>
        <a
          href={article.source_url}
          target="_blank"
          rel="noreferrer"
          className="shrink-0 rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-2 text-sm font-semibold text-indigo-700 transition hover:bg-indigo-100"
        >
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

export default function ReportView({ report }: { report: BiasReport }) {
  const { article, plan, issue_map, dimensions, claims, overall } = report
  const plannedByKey = new Map(plan.dimensions.map((d) => [d.key, d]))

  const tabs: TabDef[] = [
    {
      id: 'summary',
      label: 'Summary',
      content: (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <dl className="mb-4 grid gap-x-6 gap-y-1 text-sm sm:grid-cols-2">
            <div>
              <dt className="inline font-semibold text-slate-500">Topic: </dt>
              <dd className="inline text-slate-700">{plan.topic}</dd>
            </div>
            <div>
              <dt className="inline font-semibold text-slate-500">Main subject: </dt>
              <dd className="inline text-slate-700">{plan.main_subject}</dd>
            </div>
            <div>
              <dt className="inline font-semibold text-slate-500">Type: </dt>
              <dd className="inline text-slate-700">{plan.article_type}</dd>
            </div>
          </dl>
          <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-400">
            What the article says
          </h3>
          <p className="text-sm leading-relaxed text-slate-700">{plan.summary}</p>
          {plan.central_claims.length > 0 && (
            <ul className="mt-3 list-inside list-disc space-y-1 text-sm text-slate-600">
              {plan.central_claims.map((c, i) => (
                <li key={i}>{c}</li>
              ))}
            </ul>
          )}
        </div>
      ),
    },
    {
      id: 'debate',
      label: 'The debate',
      content: <IssueMapView map={issue_map} />,
    },
    {
      id: 'claims',
      label: 'Claims',
      count: claims.length,
      content:
        claims.length > 0 ? (
          <ClaimsView claims={claims} />
        ) : (
          <p className="text-sm text-slate-500">No material claims were extracted.</p>
        ),
    },
    {
      id: 'dimensions',
      label: 'Dimensions',
      count: dimensions.length,
      content: (
        <div className="space-y-3">
          {dimensions.map((d) => (
            <DimensionCard key={d.key} a={d} planned={plannedByKey.get(d.key)} />
          ))}
        </div>
      ),
    },
    {
      id: 'text',
      label: 'Source text',
      content: (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-400">
            The exact text we analyzed
          </h3>
          {article.truncated && (
            <p className="mb-2 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">
              This was truncated to fit the model’s budget — the analysis saw the first{' '}
              {article.word_count.toLocaleString()} words.
            </p>
          )}
          <div className="max-h-[28rem] overflow-y-auto whitespace-pre-wrap rounded-lg bg-slate-50 p-3 text-sm leading-relaxed text-slate-700">
            {article.text}
          </div>
        </div>
      ),
    },
  ]

  return (
    <div className="animate-fade-in space-y-6">
      {/* Where it came from */}
      <SourceBar report={report} />

      {/* Verdict header */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col items-center gap-6 md:flex-row md:items-start">
          <ScoreGauge score={overall.overall_score} label={overall.fairness_label} />
          <div className="flex-1">
            <h2 className="text-lg font-bold text-slate-800">{article.title}</h2>
            <div className="mt-2 flex flex-wrap gap-2 text-xs">
              <span className="rounded-full bg-slate-100 px-2.5 py-1 text-slate-600">
                {plan.article_type}
              </span>
              <span className="rounded-full bg-slate-100 px-2.5 py-1 text-slate-600">
                Lean: {leanLabel(overall.political_lean)} ({overall.lean_confidence}%)
              </span>
              {overall.adopted_framing && (
                <span className="rounded-full bg-slate-100 px-2.5 py-1 text-slate-600">
                  Framing: {overall.adopted_framing}
                </span>
              )}
              {overall.both_sidesing && (
                <span className="rounded-full bg-amber-100 px-2.5 py-1 font-medium text-amber-800">
                  ⚠ both-sides a settled issue
                </span>
              )}
              {overall.false_consensus && (
                <span className="rounded-full bg-amber-100 px-2.5 py-1 font-medium text-amber-800">
                  ⚠ presents contested as settled
                </span>
              )}
            </div>

            {/* Two axes */}
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <AxisBar
                label="Presentation"
                score={overall.presentation_score}
                hint="How it says it — language, framing, tone, balance"
              />
              <AxisBar
                label="Substance"
                score={overall.substantive_score}
                hint="What it says — claims, facts, coverage vs the map"
              />
            </div>

            <p className="mt-4 text-sm leading-relaxed text-slate-700">
              {overall.executive_summary}
            </p>
          </div>
        </div>

        {(overall.key_strengths.length > 0 || overall.key_concerns.length > 0) && (
          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <div className="rounded-xl bg-green-50 p-4">
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-green-700">
                Strengths
              </h4>
              <ul className="list-inside list-disc space-y-1 text-sm text-green-900">
                {overall.key_strengths.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
            <div className="rounded-xl bg-red-50 p-4">
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-red-700">
                Concerns
              </h4>
              <ul className="list-inside list-disc space-y-1 text-sm text-red-900">
                {overall.key_concerns.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>

      {/* Detail sections — tabbed */}
      <Tabs tabs={tabs} initialId="summary" />
    </div>
  )
}
