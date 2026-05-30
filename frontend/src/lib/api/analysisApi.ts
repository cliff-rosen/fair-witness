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
import type { AnalysisEvent, BiasReport } from '../../types/analysis'

export interface AnalyzeRequest {
  url?: string
  text?: string
  title?: string
}

export async function analyzeArticle(request: AnalyzeRequest): Promise<BiasReport> {
  const response = await api.post<BiasReport>('/api/analysis/analyze', request)
  return response.data
}

export interface StreamHandlers {
  onEvent: (event: AnalysisEvent) => void
  onError?: (message: string) => void
  onDone?: () => void
}

/**
 * Stream analysis events via the shared SSE helper. Returns a cleanup function
 * that aborts the request.
 */
export function streamAnalysis(
  request: AnalyzeRequest,
  handlers: StreamHandlers,
): () => void {
  return subscribeToSSE<AnalysisEvent>(
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
      onError: (error) => handlers.onError?.(error.message),
      onComplete: handlers.onDone,
    },
  )
}
