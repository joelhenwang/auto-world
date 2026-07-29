import { beforeEach, describe, expect, it, vi } from 'vitest'

import { WorldApiClient } from '../api/client'

const fetchMock = vi.fn<typeof fetch>()

describe('WorldApiClient', () => {
  beforeEach(() => {
    fetchMock.mockReset()
    vi.stubGlobal('fetch', fetchMock)
  })

  it('requests an observer-scoped timeline', async () => {
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify([]), {
        status: 200,
        headers: { 'content-type': 'application/json' },
      }),
    )
    const client = new WorldApiClient('https://world.test')

    await client.getTimeline('world-1', 'character-1')

    expect(fetchMock).toHaveBeenCalledWith(
      'https://world.test/api/v1/worlds/world-1/timeline?observer_id=character-1',
      expect.objectContaining({ headers: expect.any(Headers) }),
    )
  })

  it('returns empty stage2 collections when endpoints are missing', async () => {
    fetchMock.mockImplementation(async () => new Response('not found', { status: 404 }))
    const client = new WorldApiClient('https://world.test')

    await expect(client.getGoals('world-1', 'mira')).resolves.toEqual([])
    await expect(client.getMap('world-1')).resolves.toEqual({
      locations: [],
      routes: [],
      travel: [],
    })
    await expect(client.getDirectorPanel('world-1')).resolves.toBeNull()
  })

  it('submits player intent fields rather than canonical effects', async () => {
    fetchMock.mockResolvedValue(
      new Response(
        JSON.stringify({
          command_id: 'command-1',
          status: 'pending',
          already_existed: false,
        }),
        { status: 202, headers: { 'content-type': 'application/json' } },
      ),
    )
    const client = new WorldApiClient()

    await client.submitAction('world-1', 'mira', {
      session_id: 'session-1',
      controller_id: 'player-one',
      idempotency_key: 'action-one',
      action_family: 'communicate',
      description: 'Ask about the bridge.',
      utterance: 'Is it open?',
      target_entity_ids: ['dain'],
      target_location_id: null,
    })

    const request = fetchMock.mock.calls[0]?.[1]
    expect(request?.method).toBe('POST')
    expect(JSON.parse(String(request?.body))).toEqual({
      session_id: 'session-1',
      controller_id: 'player-one',
      idempotency_key: 'action-one',
      action_family: 'communicate',
      description: 'Ask about the bridge.',
      utterance: 'Is it open?',
      target_entity_ids: ['dain'],
      target_location_id: null,
    })
    expect(String(request?.body)).not.toContain('effects')
  })
})
