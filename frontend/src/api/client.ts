import type { components } from './generated/schema'
import type {
  BeliefRead,
  CommitmentRead,
  DiaryEntryRead,
  DirectorPanelRead,
  GoalRead,
  MapStateRead,
  NpcLifecycleRead,
  PlanRead,
  RelationshipRead,
  RunProgressRead,
  SummaryRead,
} from './stage2-types'
import type { ArcRead, FactionRead, LongTermMemoryRead, MonthRunRead } from './stage3-types'
import type {
  GalleryItemRead,
  ImageJobRead,
  VisualProfileRead,
  WorkerHealthPanelRead,
} from './stage4-types'

export type WorldRead = components['schemas']['WorldRead']
export type ClockRead = components['schemas']['ClockRead']
export type AdvancePhaseResponse = components['schemas']['AdvancePhaseResponse']
export type CharacterSummaryRead = components['schemas']['CharacterSummaryRead']
export type PlayerControlRead = components['schemas']['PlayerControlRead']
export type PlayerActionRequest = components['schemas']['PlayerActionRequest']
export type PlayerActionResponse = components['schemas']['PlayerActionResponse']
export type RuntimeCommandResponse = components['schemas']['RuntimeCommandResponse']
export type StreamEventRead = components['schemas']['StreamEventRead']

export type {
  BeliefRead,
  CommitmentRead,
  DiaryEntryRead,
  DirectorPanelRead,
  GoalRead,
  MapStateRead,
  NpcLifecycleRead,
  PlanRead,
  RelationshipRead,
  RunProgressRead,
  SummaryRead,
}

export type { ArcRead, FactionRead, LongTermMemoryRead, MonthRunRead }

export type {
  GalleryItemRead,
  HostHealthRead,
  ImageJobRead,
  ModelHealthRead,
  VisualProfileRead,
  WorkerHealthPanelRead,
  WorkerHealthRead,
} from './stage4-types'

export { NONCANONICAL_ILLUSTRATION_BANNER } from './stage4-types'

function emptyWorkerHealth(): WorkerHealthPanelRead {
  return { hosts: [], workers: [], models: [] }
}

type RequestOptions = Omit<RequestInit, 'body'> & {
  body?: object
}

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

function emptyMap(): MapStateRead {
  return { locations: [], routes: [], travel: [] }
}

export class WorldApiClient {
  private readonly baseUrl: string

  constructor(baseUrl = '') {
    this.baseUrl = baseUrl
  }

  getWorldBySlug(slug: string): Promise<WorldRead> {
    return this.request(`/worlds/by-slug/${encodeURIComponent(slug)}`)
  }

  getClock(worldId: string): Promise<ClockRead> {
    return this.request(`/worlds/${worldId}/clock`)
  }

  getCharacters(worldId: string): Promise<CharacterSummaryRead[]> {
    return this.request(`/api/v1/worlds/${worldId}/characters`)
  }

  getTimeline(
    worldId: string,
    observerId?: string,
    filters?: { characterId?: string; locationId?: string },
  ): Promise<StreamEventRead[]> {
    const params = new URLSearchParams()
    if (observerId) {
      params.set('observer_id', observerId)
    }
    if (filters?.characterId) {
      params.set('character_id', filters.characterId)
    }
    if (filters?.locationId) {
      params.set('location_id', filters.locationId)
    }
    const query = params.toString() ? `?${params}` : ''
    return this.request(`/api/v1/worlds/${worldId}/timeline${query}`)
  }

  /** Stage 2 run progress; null when endpoint is not yet available. */
  getRunProgress(worldId: string): Promise<RunProgressRead | null> {
    return this.optionalRequest(`/api/v1/worlds/${worldId}/run-progress`)
  }

  getMap(worldId: string, observerId?: string): Promise<MapStateRead> {
    const query = observerId
      ? `?observer_id=${encodeURIComponent(observerId)}`
      : ''
    return this.optionalList(
      `/api/v1/worlds/${worldId}/map${query}`,
      emptyMap,
      (raw) => {
        if (Array.isArray(raw)) {
          return { locations: raw as MapStateRead['locations'], routes: [], travel: [] }
        }
        const body = raw as Partial<MapStateRead>
        return {
          locations: body.locations ?? [],
          routes: body.routes ?? [],
          travel: body.travel ?? [],
        }
      },
    )
  }

  getGoals(worldId: string, characterId: string): Promise<GoalRead[]> {
    return this.optionalArray(
      `/api/v1/worlds/${worldId}/characters/${characterId}/goals`,
    )
  }

  getPlans(worldId: string, characterId: string): Promise<PlanRead[]> {
    return this.optionalArray(
      `/api/v1/worlds/${worldId}/characters/${characterId}/plans`,
    )
  }

  getCommitments(worldId: string, characterId: string): Promise<CommitmentRead[]> {
    return this.optionalArray(
      `/api/v1/worlds/${worldId}/characters/${characterId}/commitments`,
    )
  }

  getRelationships(
    worldId: string,
    characterId: string,
  ): Promise<RelationshipRead[]> {
    return this.optionalArray(
      `/api/v1/worlds/${worldId}/characters/${characterId}/relationships`,
    )
  }

  /**
   * Perspective-filtered beliefs. Returns [] on 404; throws ApiError on 403
   * so the UI can hide unauthorized watcher-only content.
   */
  getBeliefs(
    worldId: string,
    characterId: string,
    observerId?: string,
  ): Promise<BeliefRead[]> {
    const query = observerId
      ? `?observer_id=${encodeURIComponent(observerId)}`
      : ''
    return this.requestOptionalArray(
      `/api/v1/worlds/${worldId}/characters/${characterId}/beliefs${query}`,
    )
  }

  getDiary(worldId: string, characterId: string): Promise<DiaryEntryRead[]> {
    return this.optionalArray(
      `/api/v1/worlds/${worldId}/characters/${characterId}/diary`,
    )
  }

  getSummaries(worldId: string, characterId: string): Promise<SummaryRead[]> {
    return this.optionalArray(
      `/api/v1/worlds/${worldId}/characters/${characterId}/summaries`,
    )
  }

  getNpcs(worldId: string): Promise<NpcLifecycleRead[]> {
    return this.optionalArray(`/api/v1/worlds/${worldId}/npcs`)
  }

  /**
   * Director metrics/hooks — watcher/director only.
   * Returns null on 403/404 so player mode never surfaces the panel data.
   */
  getDirectorPanel(worldId: string): Promise<DirectorPanelRead | null> {
    return this.optionalRequest(`/api/v1/worlds/${worldId}/director`, undefined, [
      403,
      404,
      501,
    ])
  }

  getMonthRuns(worldId: string): Promise<MonthRunRead[]> {
    return this.optionalArray(`/api/v1/worlds/${worldId}/month-runs`)
  }

  getArcs(worldId: string): Promise<ArcRead[]> {
    return this.optionalArray(`/api/v1/worlds/${worldId}/arcs`)
  }

  getFactions(worldId: string): Promise<FactionRead[]> {
    return this.optionalArray(`/api/v1/worlds/${worldId}/factions`)
  }

  getMemories(worldId: string, characterId: string): Promise<LongTermMemoryRead[]> {
    return this.optionalArray(
      `/api/v1/worlds/${worldId}/characters/${characterId}/memories`,
    )
  }

  /** Stage 4 host/worker/model health; empty when admin API is not yet available. */
  getWorkerHealth(worldId: string): Promise<WorkerHealthPanelRead> {
    return this.optionalList(
      `/api/v1/worlds/${worldId}/ops/workers`,
      emptyWorkerHealth,
      (raw) => {
        if (raw && typeof raw === 'object' && !Array.isArray(raw)) {
          const panel = raw as Partial<WorkerHealthPanelRead>
          return {
            hosts: Array.isArray(panel.hosts) ? panel.hosts : [],
            workers: Array.isArray(panel.workers) ? panel.workers : [],
            models: Array.isArray(panel.models) ? panel.models : [],
          }
        }
        return emptyWorkerHealth()
      },
    )
  }

  /** Stage 4 gallery items; empty until S4-API-001 lands. */
  getGallery(worldId: string): Promise<GalleryItemRead[]> {
    return this.optionalArray(`/api/v1/worlds/${worldId}/gallery`)
  }

  /** Stage 4 image job queue; empty until S4-API-001 lands. */
  getImageJobs(worldId: string): Promise<ImageJobRead[]> {
    return this.optionalArray(`/api/v1/worlds/${worldId}/image-jobs`)
  }

  /** Stage 4 visual profiles; empty until S4-API-001 lands. */
  getVisualProfiles(worldId: string): Promise<VisualProfileRead[]> {
    return this.optionalArray(`/api/v1/worlds/${worldId}/visual-profiles`)
  }

  advance(worldId: string): Promise<AdvancePhaseResponse> {
    return this.request(`/api/v1/worlds/${worldId}/advance`, { method: 'POST' })
  }

  pause(worldId: string): Promise<RuntimeCommandResponse> {
    return this.request(`/api/v1/worlds/${worldId}/pause`, {
      method: 'POST',
      body: { mode: 'after_safe_boundary' },
    })
  }

  resume(worldId: string): Promise<RuntimeCommandResponse> {
    return this.request(`/api/v1/worlds/${worldId}/resume`, { method: 'POST' })
  }

  acquireControl(
    worldId: string,
    characterId: string,
    controllerId: string,
  ): Promise<PlayerControlRead> {
    return this.request(
      `/api/v1/worlds/${worldId}/characters/${characterId}/player/acquire`,
      {
        method: 'POST',
        body: {
          controller_id: controllerId,
          idempotency_key: `web-control:${controllerId}:${characterId}`,
        },
      },
    )
  }

  releaseControl(
    worldId: string,
    characterId: string,
    sessionId: string,
    controllerId: string,
  ): Promise<PlayerControlRead> {
    return this.request(
      `/api/v1/worlds/${worldId}/characters/${characterId}/player/release`,
      {
        method: 'POST',
        body: {
          controller_id: controllerId,
          session_id: sessionId,
        },
      },
    )
  }

  submitAction(
    worldId: string,
    characterId: string,
    request: PlayerActionRequest,
  ): Promise<PlayerActionResponse> {
    return this.request(
      `/api/v1/worlds/${worldId}/characters/${characterId}/player/action`,
      {
        method: 'POST',
        body: request,
      },
    )
  }

  private async optionalArray<T>(path: string): Promise<T[]> {
    return this.requestOptionalArray(path)
  }

  private async requestOptionalArray<T>(path: string): Promise<T[]> {
    try {
      const data = await this.request<T[] | { data: T[] }>(path)
      return Array.isArray(data) ? data : (data.data ?? [])
    } catch (cause) {
      if (cause instanceof ApiError && (cause.status === 404 || cause.status === 501)) {
        return []
      }
      throw cause
    }
  }

  private async optionalList<T>(
    path: string,
    empty: () => T,
    normalize: (raw: unknown) => T,
  ): Promise<T> {
    try {
      const data = await this.request<unknown>(path)
      return normalize(data)
    } catch (cause) {
      if (cause instanceof ApiError && (cause.status === 404 || cause.status === 501)) {
        return empty()
      }
      throw cause
    }
  }

  private async optionalRequest<T>(
    path: string,
    fallback?: () => T,
    softStatuses: number[] = [404, 501],
  ): Promise<T | null> {
    try {
      return await this.request<T>(path)
    } catch (cause) {
      if (cause instanceof ApiError && softStatuses.includes(cause.status)) {
        return fallback ? fallback() : null
      }
      throw cause
    }
  }

  private async request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const headers = new Headers(options.headers)
    if (options.body !== undefined) {
      headers.set('content-type', 'application/json')
    }
    const response = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    })
    if (!response.ok) {
      const detail = await response.text()
      throw new ApiError(response.status, detail || response.statusText)
    }
    return (await response.json()) as T
  }
}

export const worldApi = new WorldApiClient()
