/** Minimal Stage 3 projection DTOs until OpenAPI regenerates (S3-API-001). */

export interface MonthRunRead {
  id: string
  world_id: string
  month_index: number
  status: string
  start_day_index: number
  end_day_index: number
  metrics?: Record<string, unknown>
  completed_at?: string | null
}

export interface ArcRead {
  id: string
  world_id: string
  arc_key: string
  title: string
  arc_scope: string
  status: string
  premise: string
  objective: string
  progress: number | string
  participant_entity_ids?: string[]
  dominant_genres?: string[]
  version: number
}

export interface FactionRead {
  id: string
  world_id: string
  faction_key: string
  name: string
  faction_type: string
  status: string
  territory_location_ids?: string[]
  plot_armour_bias: number | string
  version: number
}

export interface LongTermMemoryRead {
  id: string
  world_id: string
  owner_character_id: string
  memory_type: string
  content: string
  visibility: string
  status: string
  created_phase_index: number
}
