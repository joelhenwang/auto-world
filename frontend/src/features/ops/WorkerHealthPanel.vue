<script setup lang="ts">
import type { WorkerHealthPanelRead } from '../../api/stage4-types'

withDefaults(
  defineProps<{
    health?: WorkerHealthPanelRead
  }>(),
  {
    health: () => ({ hosts: [], workers: [], models: [] }),
  },
)
</script>

<template>
  <section
    class="panel worker-health-panel"
    data-testid="worker-health"
    aria-labelledby="worker-health-title"
  >
    <div class="panel-heading">
      <div>
        <p class="eyebrow">Distributed ops</p>
        <h2 id="worker-health-title">Worker health</h2>
      </div>
      <span class="count">
        {{ health.hosts.length }} host(s) · {{ health.workers.length }} worker(s)
      </span>
    </div>

    <div class="director-body">
      <section aria-labelledby="hosts-heading">
        <h3 id="hosts-heading">Hosts</h3>
        <p v-if="health.hosts.length === 0" class="empty-state compact">
          No hosts registered yet.
        </p>
        <ul v-else class="detail-list">
          <li v-for="host in health.hosts" :key="host.id">
            <strong>{{ host.host_key }}</strong>
            <span class="muted">
              {{ host.status }}
              <template v-if="host.capabilities.length">
                · {{ host.capabilities.join(', ') }}
              </template>
            </span>
          </li>
        </ul>
      </section>

      <section aria-labelledby="workers-heading">
        <h3 id="workers-heading">Workers</h3>
        <p v-if="health.workers.length === 0" class="empty-state compact">
          No workers registered yet.
        </p>
        <ul v-else class="detail-list">
          <li v-for="worker in health.workers" :key="worker.id">
            <strong>{{ worker.worker_key }}</strong>
            <span class="muted">
              {{ worker.status }}
              <template v-if="worker.capabilities.length">
                · {{ worker.capabilities.join(', ') }}
              </template>
            </span>
          </li>
        </ul>
      </section>

      <section aria-labelledby="models-heading">
        <h3 id="models-heading">Model health</h3>
        <p v-if="health.models.length === 0" class="empty-state compact">
          No model health probes recorded.
        </p>
        <ul v-else class="detail-list">
          <li v-for="model in health.models" :key="`${model.role}:${model.model_key}`">
            <strong>{{ model.model_key }}</strong>
            <span class="muted">
              {{ model.role }} · {{ model.status }}
              <template v-if="model.backend"> · {{ model.backend }}</template>
            </span>
          </li>
        </ul>
      </section>
    </div>
  </section>
</template>
