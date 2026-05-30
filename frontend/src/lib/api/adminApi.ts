import { api } from './index'
import { getAdminPassword } from '../adminAuth'

export interface AdminOverview {
  totals: { visits: number; unique_ips: number; reports: number; report_views: number }
  recent_visits: {
    ts: string | null
    ip: string | null
    path: string | null
    report_id: string | null
    referrer: string | null
    user_agent: string | null
  }[]
  top_reports: {
    report_id: string
    title: string
    view_count: number
    overall_score: number
    fairness_label: string
  }[]
  top_referrers: { referrer: string; count: number }[]
  top_paths: { path: string; count: number }[]
  by_day: { day: string; count: number }[]
}

function adminHeaders() {
  return { 'X-Admin-Password': getAdminPassword() }
}

export async function getAdminOverview(): Promise<AdminOverview> {
  const res = await api.get<AdminOverview>('/api/admin/overview', { headers: adminHeaders() })
  return res.data
}
