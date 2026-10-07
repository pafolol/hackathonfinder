export type Category = 'hackathon' | 'convocatoria' | 'aceleradora' | 'competencia' | 'fondo' | 'otro'
export type ReviewStatus = 'nueva' | 'revisada' | 'descartada'
export type Modality = 'presencial' | 'en_linea' | 'hibrido'
export type Role = 'admin' | 'staff'

export interface User {
  id: string
  email: string
  name: string
  role: Role
  is_active: boolean
  created_at: string
}

export interface ProjectInput {
  name: string
  description: string
  stage: string | null
  sector: string | null
  technologies: string[]
  team: string | null
  url: string | null
  is_active: boolean
}

export interface Project extends ProjectInput {
  id: string
  created_at: string
  updated_at: string
}

export interface Preferences {
  types: Category[]
  regions: string[]
  modalities: Modality[]
  min_prize_usd: number | null
  deadline_window_days: number
  keywords: string[]
  priority_sources: string[]
  excluded_sources: string[]
  max_results: number
}

export interface Schedule {
  enabled: boolean
  frequency: 'daily' | 'weekly'
  weekday: number
  hour: number
  timezone: string
}

export interface ContextInput {
  profile_text: string
  preferences: Preferences
  schedule: Schedule
}

export interface Context extends ContextInput {
  updated_at: string | null
  next_run_at: string | null
}

export interface Run {
  id: string
  trigger: 'manual' | 'programada'
  triggered_by: string | null
  status: 'en_curso' | 'ok' | 'error'
  started_at: string
  finished_at: string | null
  items_found: number
  items_new: number
  error: string | null
  total_tokens: number | null
}

export interface FitProject {
  project_id: string
  name: string
  note: string | null
}

export interface Opportunity {
  id: string
  title: string
  summary: string
  content: string | null
  url: string
  registration_url: string | null
  source_name: string | null
  category: Category
  importance: number
  tags: string[]
  deadline: string | null
  deadline_note: string | null
  event_start: string | null
  event_end: string | null
  registration_status: string | null
  modality: Modality | null
  city: string | null
  country: string | null
  cost: string | null
  prize_text: string | null
  prize_amount_usd: number | null
  eligibility: string | null
  requirements: string[]
  review_status: ReviewStatus
  is_saved: boolean
  discovered_at: string
  fit_projects: FitProject[]
}

export interface OpportunityFilters {
  category?: Category
  review_status?: ReviewStatus
  saved?: boolean
  project_id?: string
  q?: string
  include_closed?: boolean
  sort?: 'deadline' | 'discovered'
}
