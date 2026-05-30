/**
 * Shared-report API client. All endpoints here are PUBLIC (no passphrase) so
 * share links and feeds open for anyone.
 */

import { api } from './index'
import type { BiasReport, ReportSummary } from '../../types/analysis'

export async function getReport(id: string): Promise<BiasReport> {
  const response = await api.get<BiasReport>(`/api/reports/${id}`)
  return response.data
}

/** Newest-first feed of stored reports. Returns [] until the index is enabled. */
export async function listRecent(limit = 24): Promise<ReportSummary[]> {
  const response = await api.get<ReportSummary[]>('/api/reports', { params: { limit } })
  return response.data
}
