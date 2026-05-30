import { useState } from 'react'

interface Props {
  onSubmit: (passphrase: string) => void
  onClose: () => void
  error?: string | null
}

/**
 * Asked at the moment someone runs an analysis (not on landing). The passphrase
 * is remembered afterward, so returning users enter it once.
 */
export default function PassphraseModal({ onSubmit, onClose, error }: Props) {
  const [value, setValue] = useState('')

  function submit(e: React.FormEvent) {
    e.preventDefault()
    if (value.trim()) onSubmit(value.trim())
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={onClose}
    >
      <form
        onClick={(e) => e.stopPropagation()}
        onSubmit={submit}
        className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-xl"
      >
        <h2 className="text-lg font-bold text-slate-800">Enter the access passphrase</h2>
        <p className="mt-1 text-sm text-slate-500">
          Running an analysis calls a paid AI model, so it’s passphrase-protected. Reading and
          sharing results is always free.
        </p>
        <input
          autoFocus
          type="password"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Passphrase"
          className="mt-4 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
        />
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        <div className="mt-5 flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg px-4 py-2 text-sm font-medium text-slate-500 hover:bg-slate-100"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={!value.trim()}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 disabled:opacity-50"
          >
            Unlock &amp; analyze
          </button>
        </div>
      </form>
    </div>
  )
}
