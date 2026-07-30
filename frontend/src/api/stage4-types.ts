/** Minimal Stage 4 ops/gallery DTOs until OpenAPI regenerates (S4-API-001). */

export interface HostHealthRead {
  id: string
  host_key: string
  status: string
  capabilities: string[]
  last_seen_at?: string | null
}

export interface WorkerHealthRead {
  id: string
  host_id: string
  worker_key: string
  status: string
  capabilities: string[]
  heartbeat_at?: string | null
}

export interface ModelHealthRead {
  model_key: string
  role: string
  status: string
  backend?: string | null
  detail?: string | null
}

export interface WorkerHealthPanelRead {
  hosts: HostHealthRead[]
  workers: WorkerHealthRead[]
  models: ModelHealthRead[]
}

export interface GalleryItemRead {
  id: string
  world_id: string
  image_job_id: string
  asset_object_id: string
  asset_class: string
  display_status: string
  /** Always false for generated images — illustrations never become canon. */
  is_canonical_illustration: boolean
  qc_passed: boolean
  preview_url?: string | null
  caption?: string | null
  created_at?: string | null
}

export interface ImageJobRead {
  id: string
  world_id: string
  idempotency_key: string
  asset_class: string
  status: string
  priority: number
  attempt: number
  max_attempts: number
  workflow_version?: string | null
  seed?: number | null
  error_class?: string | null
  error_detail?: string | null
  created_at?: string | null
  started_at?: string | null
  completed_at?: string | null
}

export interface VisualProfileRead {
  id: string
  world_id: string
  subject_type: string
  subject_id: string
  subject_label?: string | null
  profile_version: number
  status: string
  reference_asset_ids: string[]
  style_summary?: string | null
}

/** Banner copy — gallery must surface this verbatim for noncanonical clarity. */
export const NONCANONICAL_ILLUSTRATION_BANNER =
  'Illustrations only — images are noncanonical and never rewrite world state.'
