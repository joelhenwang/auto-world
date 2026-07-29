/** Minimal Stage 2 projection DTOs until OpenAPI regenerates (S2-API-001). */

export const STAGE2_PHASES = [
  'dawn',
  'sunrise',
  'morning',
  'noon',
  'afternoon',
  'sunset',
  'dusk',
  'evening',
  'night',
  'midnight',
] as const

export type Stage2PhaseName = (typeof STAGE2_PHASES)[number]

export const STAGE2_RUN_DAYS = 7

export interface RunProgressRead {
  world_id: string
  day_index: number
  day_of_run: number
  total_days: number
  phase_name: string
  phase_ordinal: number
  status?: string
}

export interface GoalRead {
  id: string
  owner_character_id: string
  description: string
  category: string
  priority: number | string
  status: string
  horizon?: string | null
}

export interface PlanRead {
  id: string
  goal_id: string
  owner_character_id: string
  title: string
  status: string
  is_primary: boolean
  commitment_level?: number | string
}

export interface CommitmentRead {
  id: string
  debtor_character_id: string
  beneficiary_character_id: string
  description: string
  status: string
}

export interface RelationshipRead {
  source_character_id: string
  target_character_id: string
  familiarity: number | string
  trust: number | string
  affection: number | string
  respect: number | string
  fear: number | string
  resentment: number | string
  loyalty: number | string
  perceived_reciprocity?: number | string
}

export interface BeliefEvidenceRead {
  source_kind: string
  source_id: string
  summary?: string
}

export interface BeliefRead {
  id: string
  character_id: string
  proposition_key: string
  belief_text: string
  confidence: number | string
  status: string
  evidence?: BeliefEvidenceRead[]
  evidence_summary?: Record<string, unknown>
}

export interface DiaryEntryRead {
  id: string
  owner_character_id: string
  day_index: number
  content: string
  summary_id?: string | null
}

export interface SummaryRead {
  id: string
  owner_character_id?: string | null
  summary_type: string
  start_phase_index: number
  end_phase_index: number
  content: string
  perspective: string
}

export interface MapLocationRead {
  id: string
  name: string
  region?: string | null
  discovered?: boolean
  character_ids?: string[]
}

export interface MapRouteRead {
  id: string
  origin_location_id: string
  destination_location_id: string
  distance_units?: number | string
  base_duration_phases?: number
  status?: string
}

export interface TravelRead {
  activity_id: string
  owner_entity_id: string
  origin_location_id?: string | null
  destination_location_id?: string | null
  route_id?: string | null
  progress: number | string
  status: string
}

export interface MapStateRead {
  locations: MapLocationRead[]
  routes: MapRouteRead[]
  travel: TravelRead[]
}

export interface NpcLifecycleRead {
  character_id: string
  display_name: string
  lifecycle_status: string
  role_tags?: string[]
  activated_phase_index?: number | null
  archive_phase_index?: number | null
  ttl_until_phase?: number | null
  relevance_score?: number | string
  archive_summary?: string | null
}

export interface DirectorMetricRead {
  id: string
  metric_key: string
  metric_value: number | string
  window_start_phase: number
  window_end_phase: number
  payload?: Record<string, unknown>
}

export interface DirectorHookRead {
  id: string
  hook_key: string
  title: string
  status: string
  premise?: string
  disclosure_state?: string
}

export interface DirectorPanelRead {
  metrics: DirectorMetricRead[]
  hooks: DirectorHookRead[]
  budget_status?: string | null
  fallback_active?: boolean
}
