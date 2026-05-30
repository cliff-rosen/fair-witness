import { useEffect } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import NavBar from './NavBar'
import { trackPageView } from '../lib/api/track'

/** App chrome: persistent top nav + the active route below it. */
export default function Layout() {
  const location = useLocation()

  // Record each page view (IP + path + referrer captured server-side).
  useEffect(() => {
    trackPageView(location.pathname)
  }, [location.pathname])

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      <NavBar />
      <main>
        <Outlet />
      </main>
    </div>
  )
}
