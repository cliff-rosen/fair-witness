import axios from 'axios'
import settings from '../../config/settings'

export const api = axios.create({
  baseURL: settings.apiUrl,
  headers: { 'Content-Type': 'application/json' },
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
