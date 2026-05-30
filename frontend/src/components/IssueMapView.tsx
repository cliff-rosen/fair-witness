import type { IssueMap } from '../types/analysis'
import { structureLabel, talkingPointBadge } from '../lib/ui'

/** Renders the independent debate map the article was judged against. */
export default function IssueMapView({ map }: { map: IssueMap }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-1 flex items-center gap-2">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
          The debate (reference map)
        </h3>
        <span className="rounded-full bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-700">
          {structureLabel(map.structure)}
        </span>
      </div>
      <p className="mb-4 text-sm leading-relaxed text-slate-600">{map.structure_note}</p>

      <div className="grid gap-3 md:grid-cols-2">
        {map.sides.map((side, i) => (
          <div key={i} className="rounded-xl border border-slate-100 bg-slate-50 p-4">
            <h4 className="font-semibold text-slate-800">{side.name}</h4>
            <p className="mb-2 text-sm text-slate-600">{side.position}</p>

            {side.typical_arguments.length > 0 && (
              <ul className="mb-2 list-inside list-disc space-y-0.5 text-sm text-slate-600">
                {side.typical_arguments.map((a, j) => (
                  <li key={j}>{a}</li>
                ))}
              </ul>
            )}

            {side.talking_points.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {side.talking_points.map((tp, j) => (
                  <span
                    key={j}
                    title={tp.status}
                    className={`rounded px-2 py-0.5 text-xs ${talkingPointBadge(tp.status)}`}
                  >
                    {tp.point}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {map.settled_facts.length > 0 && (
        <div className="mt-4">
          <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-400">
            Settled facts
          </h4>
          <ul className="space-y-1 text-sm text-slate-700">
            {map.settled_facts.map((f, i) => (
              <li key={i} className="flex gap-2">
                <span className="font-mono text-xs text-slate-400">{f.confidence}%</span>
                <span>{f.fact}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {map.common_biases.length > 0 && (
        <p className="mt-4 text-xs text-slate-400">
          <span className="font-semibold">Common biases on this topic:</span>{' '}
          {map.common_biases.join('; ')}
        </p>
      )}
    </div>
  )
}
