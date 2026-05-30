// Shared access passphrase, persisted in localStorage. Required only to GENERATE
// a new analysis — viewing a shared report never reads or needs it.

const KEY = 'fw_passphrase'

export function getPassphrase(): string {
  try {
    return localStorage.getItem(KEY) ?? ''
  } catch {
    return ''
  }
}

export function setPassphrase(value: string): void {
  try {
    if (value) localStorage.setItem(KEY, value)
    else localStorage.removeItem(KEY)
  } catch {
    /* storage unavailable — passphrase just won't persist across reloads */
  }
}

export function clearPassphrase(): void {
  setPassphrase('')
}

/** Header bag for fetch-based requests (the SSE stream). Empty when unset. */
export function passphraseHeaders(): Record<string, string> {
  const p = getPassphrase()
  return p ? { 'X-App-Password': p } : {}
}
