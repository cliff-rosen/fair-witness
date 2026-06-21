/**
 * Generic, collapsible JSON renderer.
 *
 * Renders ANY value (the diagnostics screen feeds it arbitrary stage inputs and
 * outputs). Objects and arrays are native <details> so they collapse, and a
 * parent can expand/collapse the whole tree by toggling the <details> in its
 * subtree (see DiagnosticsView). Long strings are shown in full but wrap, so
 * nothing is ever truncated.
 */

type Json = unknown

const isObject = (v: Json): v is Record<string, Json> =>
  typeof v === 'object' && v !== null && !Array.isArray(v)

/** Small colored chip for known enum-ish keys — purely cosmetic. */
function badge(key: string, value: Json): string | null {
  if (typeof value === 'boolean') {
    if (key === 'verified' || key === 'ok')
      return value ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'
    return value ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-500'
  }
  if (typeof value !== 'string') return null
  const chipKeys = ['substantiation', 'location', 'handling', 'structure', 'as_presented', 'kind', 'status', 'verdict']
  return chipKeys.includes(key) ? 'bg-indigo-50 text-indigo-700' : null
}

function Primitive({ value }: { value: Json }) {
  if (value === null || value === undefined)
    return <span className="italic text-slate-400">null</span>
  if (typeof value === 'boolean')
    return <span className={`font-mono font-semibold ${value ? 'text-emerald-600' : 'text-rose-600'}`}>{String(value)}</span>
  if (typeof value === 'number')
    return <span className="font-mono font-semibold text-emerald-700">{value}</span>
  const s = String(value)
  if (/^https?:\/\//.test(s))
    return <a href={s} target="_blank" rel="noopener noreferrer" className="break-all text-amber-700 underline decoration-amber-300 hover:text-amber-800">{s}</a>
  if (s.length > 80)
    return <span className="block whitespace-pre-wrap break-words rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-slate-700">{s}</span>
  return <span className="text-slate-700">{s}</span>
}

function Row({ k, value, depth }: { k: string | number; value: Json; depth: number }) {
  const label =
    typeof k === 'number' ? (
      <span className="font-mono text-xs text-slate-400">#{k}</span>
    ) : (
      <span className="font-mono text-xs font-semibold text-violet-600">{k}</span>
    )

  if (isObject(value) || Array.isArray(value)) {
    return (
      <div className="py-0.5">
        {label}
        <div className="mt-0.5">
          <JsonView data={value} depth={depth + 1} />
        </div>
      </div>
    )
  }

  const chip = typeof k === 'string' ? badge(k, value) : null
  return (
    <div className="flex items-baseline gap-2 py-0.5">
      {label}
      <span className="min-w-0 flex-1">
        <Primitive value={value} />
      </span>
      {chip && <span className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${chip}`}>{String(value)}</span>}
    </div>
  )
}

export default function JsonView({ data, depth = 0 }: { data: Json; depth?: number }) {
  // Primitives render inline.
  if (!isObject(data) && !Array.isArray(data)) return <Primitive value={data} />

  const entries: [string | number, Json][] = Array.isArray(data)
    ? data.map((v, i) => [i, v] as [number, Json])
    : Object.entries(data)

  if (entries.length === 0)
    return <span className="font-mono text-xs text-slate-400">{Array.isArray(data) ? '[ ] empty' : '{ } empty'}</span>

  const count = Array.isArray(data) ? `[${entries.length}]` : `{${entries.length}}`
  // Short hint for collapsed objects: first id/name/title-ish field.
  let hint = ''
  if (isObject(data)) {
    const hk = ['id', 'claim_id', 'name', 'fact', 'point', 'query', 'missing', 'title'].find((k) => k in data)
    if (hk) hint = String(data[hk]).slice(0, 64)
  }

  return (
    <details open={depth < 1} className="group">
      <summary className="flex cursor-pointer list-none items-center gap-1.5 rounded py-0.5 hover:bg-slate-50">
        <span className="text-[10px] text-slate-400 transition-transform group-open:rotate-90">▶</span>
        <span className="font-mono text-xs text-slate-400">{count}</span>
        {hint && <span className="truncate text-xs text-slate-400">{hint}</span>}
      </summary>
      <div className="ml-2 border-l border-slate-200 pl-3">
        {entries.map(([k, v]) => (
          <Row key={String(k)} k={k} value={v} depth={depth} />
        ))}
      </div>
    </details>
  )
}
