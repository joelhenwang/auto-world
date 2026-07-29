<script setup lang="ts">
import { computed } from 'vue'

import type { ClockRead, RunProgressRead } from '../../api/client'
import { STAGE2_PHASES, STAGE2_RUN_DAYS } from '../../api/stage2-types'

const props = defineProps<{
  clock?: ClockRead
  progress?: RunProgressRead | null
}>()

const dayOfRun = computed(() => {
  if (props.progress?.day_of_run) {
    return Math.min(Math.max(props.progress.day_of_run, 1), STAGE2_RUN_DAYS)
  }
  if (!props.clock) {
    return 1
  }
  return Math.min(Math.max(props.clock.absolute_day_index + 1, 1), STAGE2_RUN_DAYS)
})

const totalDays = computed(
  () => props.progress?.total_days ?? STAGE2_RUN_DAYS,
)

const currentPhase = computed(() => {
  const name = props.progress?.phase_name ?? props.clock?.phase_name ?? ''
  return name.toLowerCase()
})

function phaseState(phase: string): 'done' | 'current' | 'upcoming' {
  const current = currentPhase.value
  const currentIndex = STAGE2_PHASES.indexOf(
    current as (typeof STAGE2_PHASES)[number],
  )
  const index = STAGE2_PHASES.indexOf(phase as (typeof STAGE2_PHASES)[number])
  if (currentIndex < 0 || index < 0) {
    return phase === current ? 'current' : 'upcoming'
  }
  if (index < currentIndex) return 'done'
  if (index === currentIndex) return 'current'
  return 'upcoming'
}
</script>

<template>
  <section class="day-strip panel" aria-labelledby="day-strip-title">
    <div class="panel-heading day-strip-heading">
      <div>
        <p class="eyebrow">Seven-day run</p>
        <h2 id="day-strip-title">
          Day {{ dayOfRun }}/{{ totalDays }}
        </h2>
      </div>
      <span class="count" data-testid="run-progress">
        Phase {{ clock?.phase_ordinal ?? progress?.phase_ordinal ?? '—' }} of
        {{ STAGE2_PHASES.length }}
      </span>
    </div>
    <ol class="phase-strip" aria-label="Ten-phase day strip">
      <li
        v-for="phase in STAGE2_PHASES"
        :key="phase"
        class="phase-chip"
        :data-state="phaseState(phase)"
        :aria-current="phaseState(phase) === 'current' ? 'step' : undefined"
      >
        {{ phase }}
      </li>
    </ol>
  </section>
</template>
