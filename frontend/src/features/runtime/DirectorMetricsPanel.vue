<script setup lang="ts">
import type { DirectorPanelRead } from '../../api/client'

defineProps<{
  panel: DirectorPanelRead
}>()
</script>

<template>
  <section
    class="panel director-panel"
    data-testid="director-metrics"
    aria-labelledby="director-title"
  >
    <div class="panel-heading">
      <div>
        <p class="eyebrow">Authorized mode</p>
        <h2 id="director-title">Director metrics</h2>
      </div>
      <span class="count">
        {{ panel.budget_status ?? 'budget unknown' }}
        <template v-if="panel.fallback_active"> · fallback</template>
      </span>
    </div>

    <div class="director-body">
      <section aria-labelledby="metrics-heading">
        <h3 id="metrics-heading">Trigger metrics</h3>
        <p v-if="panel.metrics.length === 0" class="empty-state compact">
          No Director metrics recorded.
        </p>
        <ul v-else class="detail-list">
          <li v-for="metric in panel.metrics" :key="metric.id">
            <strong>{{ metric.metric_key }}</strong>
            <span class="muted">
              {{ metric.metric_value }} · phases
              {{ metric.window_start_phase }}–{{ metric.window_end_phase }}
            </span>
          </li>
        </ul>
      </section>

      <section aria-labelledby="hooks-heading">
        <h3 id="hooks-heading">Hooks</h3>
        <p v-if="panel.hooks.length === 0" class="empty-state compact">
          No active hooks.
        </p>
        <ul v-else class="detail-list">
          <li v-for="hook in panel.hooks" :key="hook.id">
            <strong>{{ hook.title }}</strong>
            <span class="muted">
              {{ hook.status }} · {{ hook.hook_key }}
            </span>
          </li>
        </ul>
      </section>
    </div>
  </section>
</template>
