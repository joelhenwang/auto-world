import type { StreamEventRead } from './client'

export type ConnectionState = 'connecting' | 'live' | 'reconnecting' | 'offline'

interface StreamEventEnvelope {
  type: 'stream_event'
  sequence: number
  event: StreamEventRead
}

interface ReplayCompleteEnvelope {
  type: 'replay_complete'
  last_sequence: number
}

interface WorldStreamOptions {
  worldId: string
  observerId?: string
  afterSequence?: number
  onEvent: (event: StreamEventRead) => void
  onState: (state: ConnectionState) => void
}

export interface WorldStreamHandle {
  close: () => void
  poll: () => void
}

function websocketUrl(options: WorldStreamOptions): string {
  const scheme = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const query = new URLSearchParams({
    after_sequence: String(options.afterSequence ?? 0),
  })
  if (options.observerId) {
    query.set('observer_id', options.observerId)
  }
  return `${scheme}//${window.location.host}/ws/v1/worlds/${options.worldId}?${query}`
}

function isStreamEvent(message: unknown): message is StreamEventEnvelope {
  if (typeof message !== 'object' || message === null) {
    return false
  }
  const candidate = message as Partial<StreamEventEnvelope>
  return candidate.type === 'stream_event' && typeof candidate.sequence === 'number'
}

function isReplayComplete(message: unknown): message is ReplayCompleteEnvelope {
  if (typeof message !== 'object' || message === null) {
    return false
  }
  const candidate = message as Partial<ReplayCompleteEnvelope>
  return (
    candidate.type === 'replay_complete' &&
    typeof candidate.last_sequence === 'number'
  )
}

export function connectWorldStream(options: WorldStreamOptions): WorldStreamHandle {
  options.onState('connecting')
  const socket = new WebSocket(websocketUrl(options))
  let closed = false

  socket.addEventListener('open', () => options.onState('live'))
  socket.addEventListener('message', (raw) => {
    const message: unknown = JSON.parse(String(raw.data))
    if (isStreamEvent(message)) {
      options.onEvent(message.event)
    } else if (isReplayComplete(message)) {
      options.onState('live')
    }
  })
  socket.addEventListener('error', () => options.onState('offline'))
  socket.addEventListener('close', () => {
    if (!closed) {
      options.onState('reconnecting')
    }
  })

  return {
    close: () => {
      closed = true
      socket.close()
      options.onState('offline')
    },
    poll: () => {
      if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'poll' }))
      }
    },
  }
}
