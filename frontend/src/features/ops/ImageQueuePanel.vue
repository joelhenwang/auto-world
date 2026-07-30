<script setup lang="ts">
import type { ImageJobRead } from '../../api/stage4-types'

withDefaults(
  defineProps<{
    jobs?: ImageJobRead[]
  }>(),
  {
    jobs: () => [],
  },
)
</script>

<template>
  <section
    class="panel image-queue-panel"
    data-testid="image-queue"
    aria-labelledby="image-queue-title"
  >
    <div class="panel-heading">
      <div>
        <p class="eyebrow">Image pipeline</p>
        <h2 id="image-queue-title">Image queue</h2>
      </div>
      <span class="count">{{ jobs.length }} job(s)</span>
    </div>

    <p v-if="jobs.length === 0" class="empty-state">
      No image jobs queued. Jobs enqueue only after canonical event commit.
    </p>
    <ul v-else class="detail-list padded">
      <li v-for="job in jobs" :key="job.id">
        <strong>{{ job.asset_class }}</strong>
        <span class="muted">
          {{ job.status }} · priority {{ job.priority }} · attempt
          {{ job.attempt }}/{{ job.max_attempts }}
          <template v-if="job.workflow_version">
            · {{ job.workflow_version }}
          </template>
          <template v-if="job.seed != null"> · seed {{ job.seed }}</template>
        </span>
        <p v-if="job.error_detail" class="npc-summary">
          {{ job.error_class ?? 'error' }}: {{ job.error_detail }}
        </p>
      </li>
    </ul>
  </section>
</template>
