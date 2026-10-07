import type { Category, Modality, Opportunity, ReviewStatus } from '../api/types'

export const CATEGORY_LABELS: Record<Category, string> = {
  hackathon: 'Hackathon',
  convocatoria: 'Convocatoria',
  aceleradora: 'Aceleradora',
  competencia: 'Competencia',
  fondo: 'Fondo',
  otro: 'Otro',
}
export const CATEGORIES = Object.keys(CATEGORY_LABELS) as Category[]

export const MODALITY_LABELS: Record<Modality, string> = {
  presencial: 'Presencial',
  en_linea: 'En línea',
  hibrido: 'Híbrido',
}
export const MODALITIES = Object.keys(MODALITY_LABELS) as Modality[]

export const REVIEW_LABELS: Record<ReviewStatus, string> = {
  nueva: 'Nueva',
  revisada: 'Revisada',
  descartada: 'Descartada',
}

export const WEEKDAYS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

export function prizeLabel(opportunity: Opportunity): string | null {
  if (opportunity.prize_amount_usd) return `US$${opportunity.prize_amount_usd.toLocaleString('en-US')}`
  // Long descriptions ("no publica un premio monetario…") belong on the detail page, not in a chip.
  const text = opportunity.prize_text
  return text && text.length <= 40 ? text : null
}

export function placeLabel(opportunity: Opportunity): string | null {
  return [opportunity.city, opportunity.country].filter(Boolean).join(', ') || null
}
