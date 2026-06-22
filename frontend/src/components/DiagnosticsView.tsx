/**
 * Diagnostics screen — shows every step of a pipeline run, whole.
 *
 * One collapsible card per stage. Each card exposes the stage's full inputs
 * (system prompt + rendered user message + logical input) and its full output,
 * plus web steps for the agentic stage. Everything is a native <details>, so the
 * Expand-all / Collapse-all buttons can open or close the entire tree at once —
 * making a long run easy to scan and easy to drill into.
 */

import { useRef } from 'react'
import type { PipelineDiagnostics, StageRecord, WebStep } from '../types/analyze'
import JsonView from './JsonView'

const KIND_CHIP: Record<string, string> = {
  code: 'bg-slate-100 text-slate-600',
  structured: 'bg-sky-100 text-sky-700',
  agentic: 'bg-amber-100 text-amber-700',
}

const ACCENT: Record<string, string> = {
  code: 'border-l-slate-300',
  structured: 'border-l-sky-400',
  agentic: 'border-l-amber-400',
}

function ms(n: number): string {
  return n >= 1000 ? `${(n / 1000).toFixed(1)}s` : `${n}ms`
}

function Section({ title, children, open = false }: { title: string; children: React.ReactNode; open?: boolean }) {
  return (
    <details open={open} className="group rounded-lg border border-slate-200 bg-slate-50/60">
      <summary className="flex cursor-pointer list-none items-center gap-2 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-500 hover:text-slate-700">
        <span className="text-[10px] text-slate-400 transition-transform group-open:rotate-90">▶</span>
        {title}
      </summary>
      <div className="border-t border-slate-200 px-3 py-2.5">{children}</div>
    </details>
  )
}

function PromptBlock({ text }: { text: string }) {
  return (
    <pre className="max-h-96 overflow-auto whitespace-pre-wrap break-words rounded-md border border-slate-200 bg-white p-3 font-mono text-xs leading-relaxed text-slate-700">
      {text}
    </pre>
  )
}

function WebSteps({ steps }: { steps: WebStep[] }) {
  return (
    <ol className="space-y-1.5">
      {steps.map((s, i) => (
        <li key={i} className="flex items-start gap-2 text-sm">
          <span className={`mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded text-xs ${s.kind === 'search' ? 'bg-sky-100' : 'bg-amber-100'}`}>
            {s.kind === 'search' ? '🔍' : '📄'}
          </span>
          <span className="min-w-0">
            <span className="font-medium text-slate-700">{s.kind === 'search' ? 'search_web' : 'fetch_webpage'}</span>{' '}
            {s.query && <span className="font-mono text-xs text-slate-500">“{s.query}”</span>}
            {s.url && (
              <a href={s.url} target="_blank" rel="noopener noreferrer" className="break-all font-mono text-xs text-amber-700 underline">
                {s.url}
              </a>
            )}
            {s.result_count != null && <span className="text-xs text-slate-400"> · {s.result_count} results</span>}
            {s.title && <span className="text-xs text-slate-400"> · {s.title}</span>}
          </span>
        </li>
      ))}
      <li className="flex items-center gap-2 text-sm">
        <span className="grid h-5 w-5 place-items-center rounded bg-emerald-100 text-xs">✓</span>
        <span className="font-medium text-emerald-700">emit_result</span>
        <span className="text-xs text-slate-400">— forced structured output</span>
      </li>
    </ol>
  )
}

function Stage({ stage }: { stage: StageRecord }) {
  const isLLM = stage.kind !== 'code'
  return (
    <details open className={`group rounded-xl border border-slate-200 border-l-4 bg-white shadow-sm ${ACCENT[stage.kind] ?? ''}`}>
      <summary className="flex cursor-pointer list-none flex-wrap items-center gap-x-3 gap-y-1 px-4 py-3">
        <span className="text-xs text-slate-400 transition-transform group-open:rotate-90">▶</span>
        <span className="text-base font-bold text-slate-800">{stage.title}</span>
        <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${KIND_CHIP[stage.kind] ?? ''}`}>{stage.kind}</span>
        {!stage.ok && <span className="rounded-full bg-rose-100 px-2 py-0.5 text-[10px] font-bold uppercase text-rose-700">failed</span>}
        <span className="ml-auto flex items-center gap-3 font-mono text-xs text-slate-400">
          {stage.model && <span>{stage.model}</span>}
          <span>{ms(stage.duration_ms)}</span>
        </span>
      </summary>

      <div className="space-y-2.5 border-t border-slate-100 px-4 py-3">
        {stage.error && (
          <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{stage.error}</p>
        )}

        {/* Inputs */}
        {isLLM ? (
          <Section title="Input — system prompt">
            <PromptBlock text={stage.system_prompt ?? '(none)'} />
          </Section>
        ) : null}
        {isLLM && (
          <Section title="Input — user message (rendered)">
            <PromptBlock text={stage.user_message ?? '(none)'} />
          </Section>
        )}
        <Section title={isLLM ? 'Input — logical' : 'Input'} open={!isLLM}>
          <JsonView data={stage.input} />
        </Section>

        {/* Web activity */}
        {stage.kind === 'agentic' && stage.web_steps && stage.web_steps.length > 0 && (
          <Section title={`Web activity — ${stage.web_steps.length} step(s)`} open>
            <WebSteps steps={stage.web_steps} />
            {stage.sources.length > 0 && (
              <div className="mt-3 border-t border-slate-200 pt-2">
                <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">Sources ({stage.sources.length})</p>
                <ul className="space-y-0.5">
                  {stage.sources.map((u) => (
                    <li key={u}>
                      <a href={u} target="_blank" rel="noopener noreferrer" className="break-all font-mono text-xs text-amber-700 underline">{u}</a>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </Section>
        )}

        {/* Output */}
        <Section title="Output" open>
          <JsonView data={stage.output} />
        </Section>
      </div>
    </details>
  )
}

export default function DiagnosticsView({ data }: { data: PipelineDiagnostics }) {
  const ref = useRef<HTMLDivElement>(null)
  const setAll = (open: boolean) => {
    ref.current?.querySelectorAll('details').forEach((d) => {
      d.open = open
    })
  }

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center gap-x-4 gap-y-2 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
        <div>
          <h2 className="flex items-center gap-2 text-sm font-bold text-slate-800">
            <span>🔬</span> Pipeline diagnostics
          </h2>
          <p className="text-xs text-slate-500">
            {data.pipeline} · {data.stages.length} stages · {ms(data.total_ms)} total
          </p>
        </div>
        <div className="ml-auto flex gap-2">
          <button onClick={() => setAll(true)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:border-slate-400">
            Expand all
          </button>
          <button onClick={() => setAll(false)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:border-slate-400">
            Collapse all
          </button>
        </div>
      </div>

      <div ref={ref} className="space-y-2.5">
        {data.stages.map((s) => (
          <Stage key={s.name} stage={s} />
        ))}
      </div>
    </div>
  )
}
