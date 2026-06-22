/** Analyze pipeline API client. */

import { api } from './index'
import type { AnalyzeResult } from '../../types/analyze'

export interface AnalyzeRequest {
  url?: string
  text?: string
  title?: string
}

/** Run the analyze pipeline; returns the report + complete diagnostics. Passphrase-gated. */
export async function analyze(request: AnalyzeRequest): Promise<AnalyzeResult> {
  const response = await api.post<AnalyzeResult>('/api/analyze/run', request)
  return response.data
}

/** A fully-populated example run — no tokens spent. Public. */
export async function getSample(): Promise<AnalyzeResult> {
  const response = await api.get<AnalyzeResult>('/api/analyze/sample')
  return response.data
}
