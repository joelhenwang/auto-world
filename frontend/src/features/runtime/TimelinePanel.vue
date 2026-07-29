<script setup lang="ts">
import type { StreamEventRead } from '../../api/client'

defineProps<{
  events: StreamEventRead[]
  loading: boolean
}>()

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
      <span class="count">{{ events.length }} events</span>
    </div>

    <p v-if="loading" class="empty-state" aria-live="polite">Loading timeline…</p>
    <p v-else-if="events.length === 0" class="empty-state">
      No scenes yet. Advance the world to begin dawn.
    </p>
    <ol v-else class="timeline">
      <li v-for="event in [...events].reverse()" :key="event.id">
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
