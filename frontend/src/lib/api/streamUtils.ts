import settings from '../../config/settings'

/**
 * Subscribe to Server-Sent Events (SSE) from an endpoint.
 *
 * Ported from the TableThat `streamUtils.subscribeToSSE` pattern (line-based SSE
 * parsing, abortable via the returned cleanup function), with the auth/token
 * handling removed (Fair Witness has no auth) and POST + JSON body support added
 * so it can drive the `POST /api/analysis/stream` endpoint.
 *
 * @returns a cleanup function that aborts the connection.
 */
export function subscribeToSSE<T>(
  endpoint: string,
  onMessage: (data: T) => void,
  options?: {
    method?: 'GET' | 'POST'
    body?: unknown
    headers?: Record<string, string>
    onError?: (error: Error) => void
    onComplete?: () => void
  },
): () => void {
  const { method = 'GET', body, headers = {}, onError, onComplete } = options ?? {}
  const url = `${settings.apiUrl}${endpoint}`
  const controller = new AbortController()

  ;(async () => {
    try {
      const response = await fetch(url, {
        method,
        headers: {
          Accept: 'text/event-stream',
          ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
          ...headers,
        },
        ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
        signal: controller.signal,
        cache: 'no-cache',
      })

      if (!response.ok) {
        // Surface the backend's error detail when present.
        let detail = `HTTP ${response.status}`
        try {
          const data = await response.json()
          if (data?.detail) {
            detail = Array.isArray(data.detail)
              ? data.detail.map((e: any) => e.msg || JSON.stringify(e)).join('; ')
              : data.detail
          }
        } catch {
          /* non-JSON error body */
        }
        const err = new Error(detail) as Error & { status?: number }
        err.status = response.status
        throw err
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No response body')
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()

        if (done) {
          onComplete?.()
          break
        }

        buffer += decoder.decode(value, { stream: true })

        // Process complete SSE lines; keep the trailing partial line buffered.
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data:')) {
            const data = line.slice(5).trim()
            try {
              onMessage(JSON.parse(data) as T)
            } catch {
              // Ignore keepalive / malformed lines.
            }
          }
        }
      }
    } catch (error) {
      if ((error as Error).name !== 'AbortError') {
        onError?.(error as Error)
      }
    }
  })()

  return () => controller.abort()
}
