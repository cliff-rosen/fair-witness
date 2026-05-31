/** Live progress for the v2 pipeline — a checklist that fills in as events land. */
export interface Progress {
  stages: string[] // stage keys that have landed
  claims: number // claim checks completed
  expected: number // expected claim checks (from the argument map)
}

const STEPS: { key: string; label: string }[] = [
  { key: 'argument', label: 'Map the argument' },
  { key: 'coherence', label: 'Logic & coherence' },
  { key: 'rhetoric', label: 'Rhetoric & tone' },
  { key: 'structural', label: 'Self-consistency' },
  { key: 'reality', label: 'Build the reality map (web)' },
  { key: 'claims', label: 'Reality-check the claims (web)' },
  { key: 'omission', label: 'Omission & framing' },
  { key: 'verdict', label: 'Synthesize the verdict' },
]

export default function PipelineProgress({ progress }: { progress: Progress }) {
  const done = new Set(progress.stages)
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">Analyzing…</h3>
      <ul className="space-y-2">
        {STEPS.map((s) => {
          const isClaims = s.key === 'claims'
          const finished = isClaims ? progress.expected > 0 && progress.claims >= progress.expected : done.has(s.key)
          const active = isClaims ? progress.claims > 0 && !finished : !finished && done.size > 0
          return (
            <li key={s.key} className="flex items-center gap-3 text-sm">
              <span
                className={`flex h-5 w-5 items-center justify-center rounded-full text-xs ${
                  finished ? 'bg-green-500 text-white' : active ? 'bg-indigo-100 text-indigo-600' : 'bg-slate-100 text-slate-400'
                }`}
              >
                {finished ? '✓' : active ? '…' : ''}
              </span>
              <span className={finished ? 'text-slate-700' : active ? 'font-medium text-slate-800' : 'text-slate-400'}>
                {s.label}
                {isClaims && progress.expected > 0 && (
                  <span className="ml-1 text-slate-400">({progress.claims}/{progress.expected})</span>
                )}
              </span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
