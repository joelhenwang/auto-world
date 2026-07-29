<script setup lang="ts">
import type { ClockRead, WorldRead } from '../../api/client'
import type { ConnectionState } from '../../api/websocket'

defineProps<{
  world?: WorldRead
  clock?: ClockRead
  runtimeState: string
  connectionState: ConnectionState
  busy: boolean
}>()

defineEmits<{
  advance: []
  pause: []
  resume: []
}>()
</script>

<template>
  <header class="runtime-header">
    <div>
      <p class="eyebrow">Stage 2 · Seven-day world</p>
      <h1>{{ world?.name ?? 'Caldris: Embervale' }}</h1>
      <p v-if="clock" class="fictional-time">
        Year {{ clock.year }}, day {{ clock.day }} ·
        <strong>{{ clock.phase_name }}</strong>
      </p>
      <p v-else class="fictional-time">Loading fictional time…</p>
    </div>

    <div class="runtime-controls" aria-label="World runtime controls">
      <div class="status-row" aria-live="polite">
        <span class="status-chip">{{ runtimeState }}</span>
        <span class="connection" :data-state="connectionState">
          <span aria-hidden="true" class="connection-dot"></span>
          {{ connectionState }}
        </span>
      </div>
      <div class="button-row">
        <button type="button" :disabled="busy" @click="$emit('advance')">
          Advance phase
        </button>
        <button type="button" class="quiet" :disabled="busy" @click="$emit('pause')">
          Pause
        </button>
        <button type="button" class="quiet" :disabled="busy" @click="$emit('resume')">
          Resume
        </button>
      </div>
    </div>
  </header>
</template>
