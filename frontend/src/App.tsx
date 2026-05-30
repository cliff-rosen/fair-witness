import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import AnalyzePage from './pages/AnalyzePage'
import RecentPage from './pages/RecentPage'
import HighlightsPage from './pages/HighlightsPage'
import AboutPage from './pages/AboutPage'
import ReportPage from './pages/ReportPage'
import AdminPage from './pages/AdminPage'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<AnalyzePage />} />
        <Route path="/recent" element={<RecentPage />} />
        <Route path="/highlights" element={<HighlightsPage />} />
        <Route path="/about" element={<AboutPage />} />
        {/* Public shareable report — no passphrase required. */}
        <Route path="/r/:id" element={<ReportPage />} />
        {/* Unlisted admin tracking dashboard (separate password). */}
        <Route path="/admin" element={<AdminPage />} />
      </Route>
    </Routes>
  )
}
