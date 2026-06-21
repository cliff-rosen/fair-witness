/** v3 "best of both" API client. */

import { api } from './index'
import type { AnalyzeResult } from '../../types/boe'

export interface V3Request {
  url?: string
  text?: string
  title?: string
}

/** Run the v3 pipeline; returns the report + complete diagnostics. Passphrase-gated. */
export async function analyzeV3(request: V3Request): Promise<AnalyzeResult> {
  const response = await api.post<AnalyzeResult>('/api/v3/analyze', request)
  return response.data
}

/** A fully-populated example run — no tokens spent. Public. */
export async function getSampleV3(): Promise<AnalyzeResult> {
  const response = await api.get<AnalyzeResult>('/api/v3/sample')
  return response.data
}
