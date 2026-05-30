import type {
  AnalysisPlan,
  ExtractedArticle,
  IssueMap,
  PlannedDimension,
} from '../types/analysis'

export type Phase =
  | 'idle'
  | 'ingesting'
  | 'planning'
  | 'mapping'
  | 'evaluating'
  | 'synthesizing'
  | 'done'
  | 'error'

interface Props {
  phase: Phase
  article: ExtractedArticle | null
  plan: AnalysisPlan | null
  issueMap: IssueMap | null
  plannedDims: PlannedDimension[]
  completedKeys: Set<string>
  claimsDone: boolean
}

const ORDER: Phase[] = ['ingesting', 'planning', 'mapping', 'evaluating', 'synthesizing', 'done']

function stepStatus(step: Phase, phase: Phase): 'done' | 'active' | 'pending' {
  if (phase === 'error') return 'pending'
  const ci = ORDER.indexOf(phase)
  const si = ORDER.indexOf(step)
  if (si < ci) return 'done'
  if (si === ci) return 'active'
  return 'pending'
}

function Dot({ status }: { status: 'done' | 'active' | 'pending' }) {
  const base = 'flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold'
  if (status === 'done') return <div className={`${base} bg-green-500 text-white`}>✓</div>
  if (status === 'active')
    return <div className={`${base} animate-pulse-ring bg-indigo-500 text-white`}>●</div>
  return <div className={`${base} bg-slate-200 text-slate-400`}>○</div>
}

export default function OrchestrationProgress({
  phase,
  article,
  plan,
  issueMap,
  plannedDims,
  completedKeys,
  claimsDone,
}: Props) {
  const steps: { key: Phase; title: string; detail?: string }[] = [
    {
      key: 'ingesting',
      title: 'Ingest article',
      detail: article
        ? `${article.word_count.toLocaleString()} words${article.truncated ? ' (truncated)' : ''}`
        : undefined,
    },
    {
      key: 'planning',
      title: 'Plan analysis',
      detail: plan ? `${plan.article_type} · ${plan.dimensions.length} dimensions selected` : undefined,
    },
    {
      key: 'mapping',
      title: 'Map the debate (blind to article)',
      detail: issueMap
        ? `${issueMap.structure} · ${issueMap.sides.length} sides · ${issueMap.settled_facts.length} settled facts`
        : undefined,
    },
    {
      key: 'evaluating',
      title: 'Evaluate (parallel)',
      detail:
        plannedDims.length > 0
          ? `${completedKeys.size}/${plannedDims.length} specialists · claims ${claimsDone ? '✓' : '…'}`
          : undefined,
    },
    { key: 'synthesizing', title: 'Synthesize verdict' },
  ]

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-400">
        Orchestration
      </h3>
      <div className="space-y-4">
        {steps.map((step) => {
          const status = stepStatus(step.key, phase)
          return (
            <div key={step.key}>
              <div className="flex items-center gap-3">
                <Dot status={status} />
                <span
                  className={`text-sm font-medium ${
                    status === 'pending' ? 'text-slate-400' : 'text-slate-800'
                  }`}
                >
                  {step.title}
                </span>
                {step.detail && <span className="text-xs text-slate-400">— {step.detail}</span>}
              </div>

              {/* Fan-out specialists + claims chip shown under the evaluate step */}
              {step.key === 'evaluating' && plannedDims.length > 0 && status !== 'pending' && (
                <div className="ml-9 mt-2 flex flex-wrap gap-2">
                  {plannedDims.map((d) => {
                    const done = completedKeys.has(d.key)
                    return (
                      <span
                        key={d.key}
                        className={`rounded-full px-2.5 py-1 text-xs ${
                          done
                            ? 'bg-green-100 text-green-800'
                            : 'animate-pulse-ring bg-indigo-50 text-indigo-600'
                        }`}
                      >
                        {done ? '✓ ' : '… '}
                        {d.label}
                      </span>
                    )
                  })}
                  <span
                    className={`rounded-full px-2.5 py-1 text-xs ${
                      claimsDone
                        ? 'bg-green-100 text-green-800'
                        : 'animate-pulse-ring bg-indigo-50 text-indigo-600'
                    }`}
                  >
                    {claimsDone ? '✓ ' : '… '}
                    Claim analysis
                  </span>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
