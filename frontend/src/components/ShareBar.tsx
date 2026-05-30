import { useState } from 'react'

/**
 * Share controls for a stored report: native share (mobile), Share-to-Facebook,
 * and Copy. Used after an analysis finishes and on the /r/:id page.
 */
export default function ShareBar({ reportId }: { reportId: string }) {
  const [copied, setCopied] = useState(false)
  const shareUrl = `${window.location.origin}/r/${reportId}`
  const canNativeShare = typeof navigator !== 'undefined' && typeof navigator.share === 'function'

  async function copy() {
    try {
      await navigator.clipboard.writeText(shareUrl)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      /* clipboard blocked — the link text below is selectable as a fallback */
    }
  }

  function nativeShare() {
    navigator
      .share({ title: 'Fair Witness', text: 'A fairness & bias analysis', url: shareUrl })
      .catch(() => {
        /* user cancelled or share failed — no-op */
      })
  }

  function shareToFacebook() {
    const u = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`
    // Open as a normal new tab (sized popups get blocked more aggressively).
    const win = window.open(u, '_blank', 'noopener')
    if (!win) window.location.href = u // popup blocked → navigate directly
  }

  return (
    <div className="rounded-xl border border-indigo-100 bg-indigo-50/60 px-4 py-3">
      <p className="text-sm font-semibold text-slate-700">Share this analysis</p>
      <p className="mt-0.5 break-all text-xs text-slate-500">{shareUrl}</p>
      <div className="mt-2 flex flex-col gap-2 sm:flex-row">
        <button
          onClick={shareToFacebook}
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-[#1877F2] px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-[#0f6ae0]"
        >
          <svg viewBox="0 0 24 24" className="h-4 w-4 fill-current" aria-hidden>
            <path d="M24 12.07C24 5.4 18.63 0 12 0S0 5.4 0 12.07C0 18.1 4.39 23.1 10.13 24v-8.44H7.08v-3.49h3.05V9.41c0-3.02 1.79-4.69 4.53-4.69 1.31 0 2.69.24 2.69.24v2.97h-1.52c-1.49 0-1.96.93-1.96 1.89v2.25h3.33l-.53 3.49h-2.8V24C19.61 23.1 24 18.1 24 12.07Z" />
          </svg>
          Share to Facebook
        </button>
        {canNativeShare && (
          <button
            onClick={nativeShare}
            className="inline-flex items-center justify-center rounded-lg border border-indigo-200 bg-white px-4 py-2 text-sm font-semibold text-indigo-700 transition hover:bg-indigo-50"
          >
            Share…
          </button>
        )}
        <button
          onClick={copy}
          className="inline-flex items-center justify-center rounded-lg border border-indigo-200 bg-white px-4 py-2 text-sm font-semibold text-indigo-700 transition hover:bg-indigo-50"
        >
          {copied ? 'Copied!' : 'Copy link'}
        </button>
      </div>
      <p className="mt-2 text-xs text-slate-400">
        On Facebook the link is public to open; the preview card is being improved.
      </p>
    </div>
  )
}
