import { api } from './index'

/**
 * Fire-and-forget page-view beacon → backend visit log (IP + path + referrer).
 * Never throws; tracking must not affect the UX.
 */
export function trackPageView(path: string): void {
  api
    .post('/api/track', { path, referrer: document.referrer || null })
    .catch(() => {})
}
