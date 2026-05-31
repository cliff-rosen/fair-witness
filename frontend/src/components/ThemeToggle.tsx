import { useState } from 'react'
import { getTheme, toggleTheme } from '../lib/theme'

/** Sun/moon dark-mode toggle for the top nav. */
export default function ThemeToggle() {
  const [theme, setThemeState] = useState(getTheme())
  return (
    <button
      onClick={() => setThemeState(toggleTheme())}
      title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
      aria-label="Toggle dark mode"
      className="rounded-lg px-2 py-1.5 text-base leading-none text-slate-600 transition hover:bg-slate-100 hover:text-slate-800"
    >
      {theme === 'dark' ? '☀️' : '🌙'}
    </button>
  )
}
