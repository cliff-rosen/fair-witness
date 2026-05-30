import axios from 'axios'
import settings from '../../config/settings'
import { passphraseHeaders } from '../passphrase'

export const api = axios.create({
  baseURL: settings.apiUrl,
  headers: { 'Content-Type': 'application/json' },
})

// Attach the shared passphrase (when set) to every request. The backend only
// enforces it on the analysis-generating endpoints; sending it on the public
// report GET is harmless.
api.interceptors.request.use((config) => {
  const headers = passphraseHeaders()
  if (headers['X-App-Password']) {
    config.headers.set?.('X-App-Password', headers['X-App-Password'])
  }
  return config
})

export const handleApiError = (error: any): string => {
  if (error.response) {
    const data = error.response.data
    if (Array.isArray(data?.detail)) {
      return data.detail.map((e: any) => e.msg || JSON.stringify(e)).join('; ')
    }
    return data?.detail || data?.message || 'An error occurred'
  } else if (error.request) {
    return 'No response from server'
  }
  return 'Error creating request'
}

export * from './analysisApi'
export * from './reportApi'
export * from './track'
