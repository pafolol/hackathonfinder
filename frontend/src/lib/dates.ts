const DAY_MS = 86_400_000

/** "2026-10-15" as a local calendar day. `new Date('2026-10-15')` would be UTC and can land on the 14th. */
export function parseDay(value: string): Date {
  const [year, month, day] = value.slice(0, 10).split('-').map(Number)
  return new Date(year, month - 1, day)
}

export function daysUntil(value: string): number {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  return Math.round((parseDay(value).getTime() - today.getTime()) / DAY_MS)
}

export function countdown(days: number): string {
  if (days < -1) return `Cerró hace ${-days} días`
  if (days === -1) return 'Cerró ayer'
  if (days === 0) return 'Cierra hoy'
  if (days === 1) return 'Cierra mañana'
  return `Quedan ${days} días`
}

const longDay = new Intl.DateTimeFormat('es-MX', { day: 'numeric', month: 'long', year: 'numeric' })
const monthShort = new Intl.DateTimeFormat('es-MX', { month: 'short' })
const dateTime = new Intl.DateTimeFormat('es-MX', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })

export const formatDay = (value: string) => longDay.format(parseDay(value))
export const monthAbbr = (value: string) => monthShort.format(parseDay(value)).replace('.', '')
export const formatDateTime = (value: string) => dateTime.format(new Date(value))

export function relativeTime(value: string): string {
  const minutes = Math.round((Date.now() - new Date(value).getTime()) / 60_000)
  if (minutes < 1) return 'hace un momento'
  if (minutes < 60) return `hace ${minutes} min`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `hace ${hours} h`
  const days = Math.round(hours / 24)
  if (days === 1) return 'ayer'
  if (days < 30) return `hace ${days} días`
  return formatDateTime(value)
}
