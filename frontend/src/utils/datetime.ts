/**
 * Date/time formatting utilities — all times displayed in MST (America/Denver).
 */

const MST_TZ = 'America/Denver'

/**
 * Format a UTC ISO string as a readable date + time in MST.
 * e.g. "Apr 6, 2026, 11:30 PM MST"
 */
export function formatDateTimeMST(iso: string | null | undefined): string {
  if (!iso) return '—'
  try {
    return new Intl.DateTimeFormat('en-US', {
      timeZone: MST_TZ,
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    }).format(new Date(iso)) + ' MST'
  } catch {
    return iso
  }
}

/**
 * Format just the time portion of a UTC ISO string in MST.
 * e.g. "11:30 PM MST"
 */
export function formatTimeMST(iso: string | null | undefined): string {
  if (!iso) return '—'
  try {
    return new Intl.DateTimeFormat('en-US', {
      timeZone: MST_TZ,
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    }).format(new Date(iso)) + ' MST'
  } catch {
    return iso
  }
}
