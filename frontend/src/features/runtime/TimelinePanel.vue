<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import type { CharacterSummaryRead, StreamEventRead } from '../../api/client'

const props = defineProps<{
  events: StreamEventRead[]
  characters: CharacterSummaryRead[]
  locations: { id: string; name: string }[]
  loading: boolean
}>()

const characterFilter = ref('')
const locationFilter = ref('')

const emit = defineEmits<{
  filterChange: [filters: { characterId?: string; locationId?: string }]
}>()

watch([characterFilter, locationFilter], () => {
  emit('filterChange', {
    characterId: characterFilter.value || undefined,
    locationId: locationFilter.value || undefined,
  })
})

const filteredEvents = computed(() => {
  return props.events.filter((event) => {
    if (characterFilter.value) {
      const ids = collectIds(event)
      if (!ids.includes(characterFilter.value)) {
        return false
      }
    }
    if (locationFilter.value) {
      const locationId = eventLocation(event)
      if (locationId !== locationFilter.value) {
        return false
      }
    }
    return true
  })
})

function collectIds(event: StreamEventRead): string[] {
  const ids: string[] = []
  const payload = event.payload ?? {}
  for (const key of ['character_id', 'actor_id', 'speaker_id']) {
    const value = payload[key]
    if (typeof value === 'string') ids.push(value)
  }
  const list = payload['character_ids']
  if (Array.isArray(list)) {
    for (const item of list) {
      if (typeof item === 'string') ids.push(item)
    }
  }
  const participants = payload['participant_ids']
  if (Array.isArray(participants)) {
    for (const item of participants) {
      if (typeof item === 'string') ids.push(item)
    }
  }
  return ids
}

function eventLocation(event: StreamEventRead): string | undefined {
  const payload = event.payload ?? {}
  for (const key of ['location_id', 'scene_location_id']) {
    const value = payload[key]
    if (typeof value === 'string') return value
  }
  const fictional = event.fictional_time ?? {}
  const fromTime = fictional['location_id']
  return typeof fromTime === 'string' ? fromTime : undefined
}

function eventSummary(event: StreamEventRead): string {
  for (const key of ['narration', 'canonical_summary', 'summary']) {
    const value = event.payload?.[key]
    if (typeof value === 'string' && value.trim()) {
      return value
    }
  }
  return 'A canonical scene update is available.'
}

function eventPhase(event: StreamEventRead): string {
  const phase = event.fictional_time?.['phase_name']
  return typeof phase === 'string' ? phase : 'World event'
}
</script>

<template>
  <section class="panel timeline-panel" aria-labelledby="timeline-title">
    <div class="panel-heading">
      <div>
        <p class="eyebrow">Canonical stream</p>
        <h2 id="timeline-title">Timeline</h2>
      </div>
      <span class="count">{{ filteredEvents.length }} events</span>
    </div>

    <div class="timeline-filters" aria-label="Timeline filters">
      <label>
        Character
        <select v-model="characterFilter">
          <option value="">All characters</option>
          <option
            v-for="character in characters"
            :key="character.id"
            :value="character.id"
          >
            {{ character.name }}
          </option>
        </select>
      </label>
      <label>
        Location
        <select v-model="locationFilter">
          <option value="">All locations</option>
          <option
            v-for="location in locations"
            :key="location.id"
            :value="location.id"
          >
            {{ location.name }}
          </option>
        </select>
      </label>
    </div>

    <p v-if="loading" class="empty-state" aria-live="polite">Loading timeline…</p>
    <p v-else-if="filteredEvents.length === 0" class="empty-state">
      No scenes match the current filters.
    </p>
    <ol v-else class="timeline">
      <li v-for="event in [...filteredEvents].reverse()" :key="event.id">
        <div class="scene-placeholder" aria-label="Image unavailable; text-first scene">
          <span aria-hidden="true">◇</span>
          <small>Text-first scene</small>
        </div>
        <article>
          <div class="event-meta">
            <span>{{ eventPhase(event) }}</span>
            <span>Sequence {{ event.sequence }}</span>
          </div>
          <h3>{{ event.event_type.replaceAll('.', ' ') }}</h3>
          <p>{{ eventSummary(event) }}</p>
        </article>
      </li>
    </ol>
  </section>
</template>
