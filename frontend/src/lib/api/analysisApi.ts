/**
 * Analysis API client.
 *
 * - `analyzeArticle` hits the blocking endpoint and returns the full report.
 * - `streamAnalysis` consumes the SSE endpoint over a POST (EventSource only
 *   supports GET), parsing `data:` frames into typed AnalysisEvents so the UI
 *   can render the orchestration as it unfolds.
 */

import { api } from './index'
import { subscribeToSSE } from './streamUtils'
import { passphraseHeaders } from '../passphrase'
import type { FairnessEvent, FairnessReport, ReportSummary } from '../../types/analysis'

export interface AnalyzeRequest {
  url?: string
  text?: string
  title?: string
  // Optional provenance the submitter can attach to pasted text:
  source_url?: string
  site_name?: string
  byline?: string
  published?: string
  note?: string
}

export interface PrecheckResult {
  existing: ReportSummary | null
}

/**
 * Cheap dedup check before running: has this URL/text already been analyzed?
 * Public (no passphrase) and never spends tokens.
 */
export async function precheckArticle(request: AnalyzeRequest): Promise<PrecheckResult> {
  const response = await api.post<PrecheckResult>('/api/analysis/precheck', request)
  return response.data
}

export async function analyzeArticle(request: AnalyzeRequest): Promise<FairnessReport> {
  const response = await api.post<FairnessReport>('/api/analysis/analyze', request)
  return response.data
}

export interface StreamHandlers {
  onEvent: (event: FairnessEvent) => void
  onError?: (message: string) => void
  /** Called when the backend rejects the passphrase (HTTP 401). */
  onAuthError?: (message: string) => void
  onDone?: () => void
}

/**
 * Stream analysis events via the shared SSE helper. Returns a cleanup function
 * that aborts the request. The passphrase (when set) rides along as a header.
 */
export function streamAnalysis(
  request: AnalyzeRequest,
  handlers: StreamHandlers,
): () => void {
  return subscribeToSSE<FairnessEvent>(
    '/api/analysis/stream',
    (event) => {
      handlers.onEvent(event)
      if (event.type === 'error') {
        handlers.onError?.(event.message || 'Analysis failed')
      }
    },
    {
      method: 'POST',
      body: request,
      headers: passphraseHeaders(),
      onError: (error) => {
        const status = (error as Error & { status?: number }).status
        if (status === 401) handlers.onAuthError?.(error.message)
        else handlers.onError?.(error.message)
      },
      onComplete: handlers.onDone,
    },
  )
}
