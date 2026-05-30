import { useState, type ReactNode } from 'react'

export interface TabDef {
  id: string
  label: string
  count?: number
  content: ReactNode
}

/** Minimal self-contained tab bar + panel (no external dependency). */
export default function Tabs({ tabs, initialId }: { tabs: TabDef[]; initialId?: string }) {
  const [active, setActive] = useState(initialId ?? tabs[0]?.id)
  const activeTab = tabs.find((t) => t.id === active) ?? tabs[0]

  return (
    <div>
      <div className="flex flex-wrap gap-1 border-b border-slate-200">
        {tabs.map((t) => {
          const isActive = t.id === active
          return (
            <button
              key={t.id}
              onClick={() => setActive(t.id)}
              className={`-mb-px flex items-center gap-1.5 border-b-2 px-4 py-2.5 text-sm font-medium transition ${
                isActive
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              {t.label}
              {typeof t.count === 'number' && (
                <span
                  className={`rounded-full px-1.5 py-0.5 text-xs ${
                    isActive ? 'bg-indigo-100 text-indigo-700' : 'bg-slate-100 text-slate-500'
                  }`}
                >
                  {t.count}
                </span>
              )}
            </button>
          )
        })}
      </div>
      <div className="mt-4">{activeTab?.content}</div>
    </div>
  )
}
