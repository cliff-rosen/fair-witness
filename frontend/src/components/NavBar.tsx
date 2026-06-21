import { Link, NavLink } from 'react-router-dom'
import ThemeToggle from './ThemeToggle'

const links = [
  { to: '/', label: 'Analyze', end: true },
  { to: '/recent', label: 'Recent', end: false },
  { to: '/highlights', label: 'Highlights', end: false },
  { to: '/diagnostics', label: 'Diagnostics', end: false },
  { to: '/about', label: 'About', end: false },
]

export default function NavBar() {
  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/90 backdrop-blur">
      <nav className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-x-4 gap-y-1 px-4 py-3">
        <Link
          to="/"
          className="flex shrink-0 items-center gap-2 font-bold tracking-tight text-slate-800"
        >
          <span aria-hidden className="text-indigo-600">⚖</span> Fair&nbsp;Witness
        </Link>
        <div className="flex items-center gap-0.5 text-sm sm:gap-1">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.end}
              className={({ isActive }) =>
                `rounded-lg px-2.5 py-1.5 font-medium transition sm:px-3 ${
                  isActive
                    ? 'bg-indigo-50 text-indigo-700'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-800'
                }`
              }
            >
              {l.label}
            </NavLink>
          ))}
          <ThemeToggle />
        </div>
      </nav>
    </header>
  )
}
