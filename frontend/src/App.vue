<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'

import {
  worldApi,
  type CharacterSummaryRead,
  type ClockRead,
  type StreamEventRead,
  type WorldRead,
} from './api/client'
import {
  connectWorldStream,
  type ConnectionState,
  type WorldStreamHandle,
} from './api/websocket'
import CharacterPanel from './features/runtime/CharacterPanel.vue'
import PlayerComposer from './features/runtime/PlayerComposer.vue'
import RuntimeHeader from './features/runtime/RuntimeHeader.vue'
import TimelinePanel from './features/runtime/TimelinePanel.vue'
import type { ActionDraft } from './features/runtime/types'
import { useSessionStore } from './stores/session'

const worldSlug = import.meta.env.VITE_WORLD_SLUG ?? 'caldris'
const session = useSessionStore()
const world = ref<WorldRead>()
const clock = ref<ClockRead>()
const characters = ref<CharacterSummaryRead[]>([])
const events = ref<StreamEventRead[]>([])
const loading = ref(true)
const busy = ref(false)
const error = ref('')
const commandStatus = ref('')
const runtimeState = ref('idle')
const connectionState = ref<ConnectionState>('offline')
let stream: WorldStreamHandle | undefined

const selectedCharacter = computed(() =>
  characters.value.find((character) => character.id === session.selectedCharacterId),
)

function lastSequence(): number {
  return events.value.reduce((maximum, event) => Math.max(maximum, event.sequence), 0)
}

function upsertEvent(event: StreamEventRead): void {
  const withoutDuplicate = events.value.filter((current) => current.id !== event.id)
  events.value = [...withoutDuplicate, event].sort(
    (left, right) => left.sequence - right.sequence,
  )
}

function connect(): void {
  if (!world.value) {
    return
  }
  stream?.close()
  stream = connectWorldStream({
    worldId: world.value.id,
    observerId: session.observerId,
    afterSequence: lastSequence(),
    onEvent: (event) => {
      upsertEvent(event)
      void refreshProjections()
    },
    onState: (state) => {
      connectionState.value = state
    },
  })
}

async function refreshProjections(): Promise<void> {
  if (!world.value) {
    return
  }
  const [nextClock, nextCharacters] = await Promise.all([
    worldApi.getClock(world.value.id),
    worldApi.getCharacters(world.value.id),
  ])
  clock.value = nextClock
  characters.value = nextCharacters
}

async function refreshAll(): Promise<void> {
  if (!world.value) {
    return
  }
  const [nextClock, nextCharacters, nextEvents] = await Promise.all([
    worldApi.getClock(world.value.id),
    worldApi.getCharacters(world.value.id),
    worldApi.getTimeline(world.value.id, session.observerId),
  ])
  clock.value = nextClock
  characters.value = nextCharacters
  events.value = nextEvents
}

async function load(): Promise<void> {
  loading.value = true
  error.value = ''
  try {
    world.value = await worldApi.getWorldBySlug(worldSlug)
    await refreshAll()
    connect()
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : 'Unable to load the world.'
    runtimeState.value = 'degraded'
  } finally {
    loading.value = false
  }
}

async function runCommand(action: () => Promise<void>): Promise<void> {
  busy.value = true
  error.value = ''
  try {
    await action()
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : 'The command failed.'
    runtimeState.value = 'degraded'
  } finally {
    busy.value = false
  }
}

async function advance(): Promise<void> {
  if (!world.value) return
  await runCommand(async () => {
    runtimeState.value = 'running'
    const result = await worldApi.advance(world.value!.id)
    commandStatus.value = `${result.phase_name} committed at sequence boundary`
    runtimeState.value = 'idle'
    await refreshAll()
    stream?.poll()
  })
}

async function pause(): Promise<void> {
  if (!world.value) return
  await runCommand(async () => {
    const result = await worldApi.pause(world.value!.id)
    runtimeState.value = result.status
    commandStatus.value = 'Pause requested at a safe boundary'
  })
}

async function resume(): Promise<void> {
  if (!world.value) return
  await runCommand(async () => {
    const result = await worldApi.resume(world.value!.id)
    runtimeState.value = result.status
    commandStatus.value = 'Runtime resumed'
    await refreshAll()
    stream?.poll()
  })
}

async function selectPlayer(characterId: string): Promise<void> {
  if (!world.value) return
  await runCommand(async () => {
    const current = session.control
    if (current && session.selectedCharacterId && current.character_id !== characterId) {
      await worldApi.releaseControl(
        world.value!.id,
        session.selectedCharacterId,
        current.id,
        session.controllerId,
      )
    }
    const control = await worldApi.acquireControl(
      world.value!.id,
      characterId,
      session.controllerId,
    )
    session.enterPlayer(characterId, control)
    events.value = []
    await refreshAll()
    connect()
    commandStatus.value = 'Player perspective active'
  })
}

async function selectWatcher(): Promise<void> {
  if (!world.value) return
  await runCommand(async () => {
    if (session.control && session.selectedCharacterId) {
      await worldApi.releaseControl(
        world.value!.id,
        session.selectedCharacterId,
        session.control.id,
        session.controllerId,
      )
    }
    session.enterWatcher()
    events.value = []
    await refreshAll()
    connect()
    commandStatus.value = 'Watcher perspective active'
  })
}

async function submitAction(draft: ActionDraft): Promise<void> {
  if (!world.value || !selectedCharacter.value || !session.control) return
  await runCommand(async () => {
    const result = await worldApi.submitAction(
      world.value!.id,
      selectedCharacter.value!.id,
      {
        session_id: session.control!.id,
        controller_id: session.controllerId,
        idempotency_key: `web-action:${crypto.randomUUID()}`,
        action_family: draft.actionFamily,
        description: draft.description,
        utterance: draft.utterance ?? null,
        target_entity_ids: draft.targetEntityIds,
        target_location_id: null,
      },
    )
    commandStatus.value = `Action ${result.status} · ${result.command_id}`
  })
}

onMounted(load)
onUnmounted(() => stream?.close())
</script>

<template>
  <a class="skip-link" href="#main-content">Skip to timeline</a>
  <div class="app-shell">
    <RuntimeHeader
      :world="world"
      :clock="clock"
      :runtime-state="runtimeState"
      :connection-state="connectionState"
      :busy="busy"
      @advance="advance"
      @pause="pause"
      @resume="resume"
    />

    <p v-if="error" class="error-banner" role="alert">
      <strong>Runtime unavailable.</strong> Existing story content remains readable.
      {{ error }}
    </p>
    <p v-if="commandStatus" class="command-status" aria-live="polite">
      {{ commandStatus }}
    </p>

    <main id="main-content" class="runtime-grid">
      <TimelinePanel :events="events" :loading="loading" />
      <CharacterPanel
        :characters="characters"
        :mode="session.mode"
        :selected-character-id="session.selectedCharacterId"
        :busy="busy"
        @select-player="selectPlayer"
        @select-watcher="selectWatcher"
      />
    </main>

    <PlayerComposer
      v-if="session.mode === 'player' && selectedCharacter"
      :character="selectedCharacter"
      :characters="characters"
      :busy="busy"
      @submit="submitAction"
    />

    <footer>
      Canon comes from committed world events. Model output is always a proposal.
    </footer>
  </div>
</template>
