import type { components } from './generated/schema'

export type WorldRead = components['schemas']['WorldRead']
export type ClockRead = components['schemas']['ClockRead']
export type AdvancePhaseResponse = components['schemas']['AdvancePhaseResponse']
export type CharacterSummaryRead = components['schemas']['CharacterSummaryRead']
export type PlayerControlRead = components['schemas']['PlayerControlRead']
export type PlayerActionRequest = components['schemas']['PlayerActionRequest']
export type PlayerActionResponse = components['schemas']['PlayerActionResponse']
export type RuntimeCommandResponse = components['schemas']['RuntimeCommandResponse']
export type StreamEventRead = components['schemas']['StreamEventRead']

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

  getTimeline(worldId: string, observerId?: string): Promise<StreamEventRead[]> {
    const query = observerId
      ? `?observer_id=${encodeURIComponent(observerId)}`
      : ''
    return this.request(`/api/v1/worlds/${worldId}/timeline${query}`)
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
