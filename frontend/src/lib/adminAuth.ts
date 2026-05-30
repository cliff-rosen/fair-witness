// Admin dashboard password (separate from the analyze passphrase), kept in
// localStorage so an admin enters it once.
const KEY = 'fw_admin'

export function getAdminPassword(): string {
  try {
    return localStorage.getItem(KEY) ?? ''
  } catch {
    return ''
  }
}

export function setAdminPassword(value: string): void {
  try {
    if (value) localStorage.setItem(KEY, value)
    else localStorage.removeItem(KEY)
  } catch {
    /* storage unavailable */
  }
}

export function clearAdminPassword(): void {
  setAdminPassword('')
}
