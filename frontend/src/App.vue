<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'

import {
  ApiError,
  worldApi,
  type BeliefRead,
  type CharacterSummaryRead,
  type ClockRead,
  type CommitmentRead,
  type DiaryEntryRead,
  type DirectorPanelRead,
  type GoalRead,
  type MapStateRead,
  type MonthRunRead,
  type NpcLifecycleRead,
  type PlanRead,
  type RelationshipRead,
  type RunProgressRead,
  type StreamEventRead,
  type SummaryRead,
  type WorldRead,
  type ArcRead,
  type FactionRead,
  type GalleryItemRead,
  type ImageJobRead,
  type VisualProfileRead,
  type WorkerHealthPanelRead,
} from './api/client'
import {
  connectWorldStream,
  type ConnectionState,
  type WorldStreamHandle,
} from './api/websocket'
import CharacterPanel from './features/runtime/CharacterPanel.vue'
import DayStrip from './features/runtime/DayStrip.vue'
import DiaryPanel from './features/runtime/DiaryPanel.vue'
import DirectorMetricsPanel from './features/runtime/DirectorMetricsPanel.vue'
import MapPanel from './features/runtime/MapPanel.vue'
import MonthExplorerPanel from './features/runtime/MonthExplorerPanel.vue'
import NpcLifecyclePanel from './features/runtime/NpcLifecyclePanel.vue'
import PlayerComposer from './features/runtime/PlayerComposer.vue'
import RuntimeHeader from './features/runtime/RuntimeHeader.vue'
import TimelinePanel from './features/runtime/TimelinePanel.vue'
import ImageGalleryPanel from './features/ops/ImageGalleryPanel.vue'
import ImageQueuePanel from './features/ops/ImageQueuePanel.vue'
import VisualProfilePanel from './features/ops/VisualProfilePanel.vue'
import WorkerHealthPanel from './features/ops/WorkerHealthPanel.vue'
import type { ActionDraft } from './features/runtime/types'
import { useSessionStore } from './stores/session'

const worldSlug = import.meta.env.VITE_WORLD_SLUG ?? 'caldris'
const session = useSessionStore()
const world = ref<WorldRead>()
const clock = ref<ClockRead>()
const progress = ref<RunProgressRead | null>(null)
const characters = ref<CharacterSummaryRead[]>([])
const events = ref<StreamEventRead[]>([])
const goals = ref<GoalRead[]>([])
const plans = ref<PlanRead[]>([])
const commitments = ref<CommitmentRead[]>([])
const relationships = ref<RelationshipRead[]>([])
const beliefs = ref<BeliefRead[]>([])
const beliefsAuthorized = ref(true)
const diaries = ref<DiaryEntryRead[]>([])
const summaries = ref<SummaryRead[]>([])
const mapState = ref<MapStateRead>({ locations: [], routes: [], travel: [] })
const npcs = ref<NpcLifecycleRead[]>([])
const directorPanel = ref<DirectorPanelRead | null>(null)
const monthRuns = ref<MonthRunRead[]>([])
const arcs = ref<ArcRead[]>([])
const factions = ref<FactionRead[]>([])
const workerHealth = ref<WorkerHealthPanelRead>({ hosts: [], workers: [], models: [] })
const galleryItems = ref<GalleryItemRead[]>([])
const imageJobs = ref<ImageJobRead[]>([])
const visualProfiles = ref<VisualProfileRead[]>([])
const memoryCount = ref(0)
const focusCharacterId = ref<string>()
const timelineFilters = ref<{ characterId?: string; locationId?: string }>({})
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

const focusedCharacter = computed(() =>
  characters.value.find((character) => character.id === focusCharacterId.value),
)

const characterNames = computed(() =>
  Object.fromEntries(characters.value.map((character) => [character.id, character.name])),
)

const locationOptions = computed(() =>
  mapState.value.locations.map((location) => ({
    id: location.id,
    name: location.name,
  })),
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

async function refreshCharacterDetail(characterId: string | undefined): Promise<void> {
  if (!world.value || !characterId) {
    goals.value = []
    plans.value = []
    commitments.value = []
    relationships.value = []
    beliefs.value = []
    beliefsAuthorized.value = true
    diaries.value = []
    summaries.value = []
    memoryCount.value = 0
    return
  }

  const [
    nextGoals,
    nextPlans,
    nextCommitments,
    nextRelationships,
    nextDiaries,
    nextSummaries,
    nextMemories,
  ] = await Promise.all([
    worldApi.getGoals(world.value.id, characterId),
    worldApi.getPlans(world.value.id, characterId),
    worldApi.getCommitments(world.value.id, characterId),
    worldApi.getRelationships(world.value.id, characterId),
    worldApi.getDiary(world.value.id, characterId),
    worldApi.getSummaries(world.value.id, characterId),
    worldApi.getMemories(world.value.id, characterId),
  ])
  goals.value = nextGoals
  plans.value = nextPlans
  commitments.value = nextCommitments
  relationships.value = nextRelationships
  diaries.value = nextDiaries
  summaries.value = nextSummaries
  memoryCount.value = nextMemories.length

  // Player may only load beliefs for the controlled character; other views are unauthorized.
  const playerUnauthorized =
    session.mode === 'player' && characterId !== session.selectedCharacterId
  if (playerUnauthorized) {
    beliefs.value = []
    beliefsAuthorized.value = false
    return
  }

  try {
    beliefs.value = await worldApi.getBeliefs(
      world.value.id,
      characterId,
      session.observerId,
    )
    beliefsAuthorized.value = true
  } catch (cause) {
    if (cause instanceof ApiError && (cause.status === 403 || cause.status === 401)) {
      beliefs.value = []
      beliefsAuthorized.value = false
      return
    }
    throw cause
  }
}

async function refreshProjections(): Promise<void> {
  if (!world.value) {
    return
  }
  const [nextClock, nextCharacters, nextProgress, nextMap, nextNpcs, nextMonths, nextArcs, nextFactions, nextHealth, nextGallery, nextJobs, nextProfiles] =
    await Promise.all([
      worldApi.getClock(world.value.id),
      worldApi.getCharacters(world.value.id),
      worldApi.getRunProgress(world.value.id),
      worldApi.getMap(world.value.id, session.observerId),
      worldApi.getNpcs(world.value.id),
      worldApi.getMonthRuns(world.value.id),
      worldApi.getArcs(world.value.id),
      worldApi.getFactions(world.value.id),
      worldApi.getWorkerHealth(world.value.id),
      worldApi.getGallery(world.value.id),
      worldApi.getImageJobs(world.value.id),
      worldApi.getVisualProfiles(world.value.id),
    ])
  clock.value = nextClock
  characters.value = nextCharacters
  progress.value = nextProgress
  mapState.value = nextMap
  npcs.value = nextNpcs
  monthRuns.value = nextMonths
  arcs.value = nextArcs
  factions.value = nextFactions
  workerHealth.value = nextHealth
  galleryItems.value = nextGallery
  imageJobs.value = nextJobs
  visualProfiles.value = nextProfiles

  if (session.canViewDirector) {
    try {
      directorPanel.value = await worldApi.getDirectorPanel(world.value.id)
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 403) {
        directorPanel.value = null
      } else {
        throw cause
      }
    }
  } else {
    directorPanel.value = null
  }

  await refreshCharacterDetail(focusCharacterId.value)
}

async function refreshAll(): Promise<void> {
  if (!world.value) {
    return
  }
  const [
    nextClock,
    nextCharacters,
    nextEvents,
    nextProgress,
    nextMap,
    nextNpcs,
    nextMonths,
    nextArcs,
    nextFactions,
    nextHealth,
    nextGallery,
    nextJobs,
    nextProfiles,
  ] = await Promise.all([
    worldApi.getClock(world.value.id),
    worldApi.getCharacters(world.value.id),
    worldApi.getTimeline(
      world.value.id,
      session.observerId,
      timelineFilters.value,
    ),
    worldApi.getRunProgress(world.value.id),
    worldApi.getMap(world.value.id, session.observerId),
    worldApi.getNpcs(world.value.id),
    worldApi.getMonthRuns(world.value.id),
    worldApi.getArcs(world.value.id),
    worldApi.getFactions(world.value.id),
    worldApi.getWorkerHealth(world.value.id),
    worldApi.getGallery(world.value.id),
    worldApi.getImageJobs(world.value.id),
    worldApi.getVisualProfiles(world.value.id),
  ])
  clock.value = nextClock
  characters.value = nextCharacters
  events.value = nextEvents
  progress.value = nextProgress
  mapState.value = nextMap
  npcs.value = nextNpcs
  monthRuns.value = nextMonths
  arcs.value = nextArcs
  factions.value = nextFactions
  workerHealth.value = nextHealth
  galleryItems.value = nextGallery
  imageJobs.value = nextJobs
  visualProfiles.value = nextProfiles

  if (session.canViewDirector) {
    try {
      directorPanel.value = await worldApi.getDirectorPanel(world.value.id)
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 403) {
        directorPanel.value = null
      } else {
        throw cause
      }
    }
  } else {
    directorPanel.value = null
  }

  if (!focusCharacterId.value && characters.value[0]) {
    focusCharacterId.value = session.selectedCharacterId ?? characters.value[0].id
  }
  await refreshCharacterDetail(focusCharacterId.value)
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
    focusCharacterId.value = characterId
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

async function selectDirector(): Promise<void> {
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
    session.enterDirector()
    events.value = []
    await refreshAll()
    connect()
    commandStatus.value = 'Director perspective active'
  })
}

async function onFocusCharacter(characterId: string): Promise<void> {
  focusCharacterId.value = characterId
  await refreshCharacterDetail(characterId)
}

async function onTimelineFilter(filters: {
  characterId?: string
  locationId?: string
}): Promise<void> {
  timelineFilters.value = filters
  if (!world.value) return
  try {
    events.value = await worldApi.getTimeline(
      world.value.id,
      session.observerId,
      filters,
    )
  } catch {
    // Client-side filter in TimelinePanel still applies if server ignores params.
  }
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

    <DayStrip :clock="clock" :progress="progress" />

    <p v-if="error" class="error-banner" role="alert">
      <strong>Runtime unavailable.</strong> Existing story content remains readable.
      {{ error }}
    </p>
    <p v-if="commandStatus" class="command-status" aria-live="polite">
      {{ commandStatus }}
    </p>

    <main id="main-content" class="runtime-grid">
      <TimelinePanel
        :events="events"
        :characters="characters"
        :locations="locationOptions"
        :loading="loading"
        @filter-change="onTimelineFilter"
      />
      <CharacterPanel
        :characters="characters"
        :mode="session.mode"
        :selected-character-id="session.selectedCharacterId"
        :focus-character-id="focusCharacterId"
        :busy="busy"
        :goals="goals"
        :plans="plans"
        :commitments="commitments"
        :relationships="relationships"
        :beliefs="beliefs"
        :beliefs-authorized="beliefsAuthorized"
        @select-player="selectPlayer"
        @select-watcher="selectWatcher"
        @select-director="selectDirector"
        @focus-character="onFocusCharacter"
      />
    </main>

    <div class="secondary-grid">
      <DiaryPanel
        :character-name="focusedCharacter?.name"
        :diaries="diaries"
        :summaries="summaries"
      />
      <MapPanel :map="mapState" :character-names="characterNames" />
      <NpcLifecyclePanel :npcs="npcs" />
      <MonthExplorerPanel
        :month-runs="monthRuns"
        :memory-count="memoryCount"
        :arcs="arcs"
        :factions="factions"
        :character-name="focusedCharacter?.name"
      />
      <WorkerHealthPanel :health="workerHealth" />
      <ImageGalleryPanel :items="galleryItems" />
      <ImageQueuePanel :jobs="imageJobs" />
      <VisualProfilePanel :profiles="visualProfiles" />
      <DirectorMetricsPanel
        v-if="session.canViewDirector && directorPanel"
        :panel="directorPanel"
      />
    </div>

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
