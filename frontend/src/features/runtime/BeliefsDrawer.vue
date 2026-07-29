<script setup lang="ts">
import { ref, watch } from 'vue'

import type { BeliefRead } from '../../api/client'
import type { UserMode } from '../../stores/session'

const props = defineProps<{
  beliefs: BeliefRead[]
  mode: UserMode
  /** False when player is unauthorized for watcher-only belief views. */
  authorized: boolean
  characterName?: string
}>()

const open = ref(false)

watch(
  () => props.authorized,
  (next) => {
    if (!next) {
      open.value = false
    }
  },
)

function confidenceLabel(value: number | string): string {
  const numeric = Number(value)
  if (Number.isNaN(numeric)) return String(value)
  return `${Math.round(numeric * 100)}%`
}
</script>

<template>
  <section
    v-if="authorized"
    class="beliefs-drawer"
    data-testid="beliefs-drawer"
    :data-mode="mode"
    aria-labelledby="beliefs-title"
  >
    <button
      type="button"
      class="drawer-toggle"
      :aria-expanded="open"
      @click="open = !open"
    >
      <span>
        <span class="eyebrow">Perspective knowledge</span>
        <strong id="beliefs-title">
          Beliefs{{ characterName ? ` · ${characterName}` : '' }}
        </strong>
      </span>
      <span class="count">{{ beliefs.length }}</span>
    </button>

    <div v-if="open" class="drawer-body">
      <p v-if="beliefs.length === 0" class="empty-state compact">
        No beliefs available for this perspective yet.
      </p>
      <ul v-else class="belief-list">
        <li v-for="belief in beliefs" :key="belief.id">
          <p class="belief-text">{{ belief.belief_text }}</p>
          <div class="event-meta">
            <span>{{ belief.status }}</span>
            <span>Confidence {{ confidenceLabel(belief.confidence) }}</span>
          </div>
          <p v-if="belief.evidence?.length" class="provenance">
            Provenance:
            <span
              v-for="(item, index) in belief.evidence"
              :key="`${item.source_kind}-${item.source_id}`"
            >
              {{ item.source_kind
              }}{{ index < (belief.evidence?.length ?? 0) - 1 ? ', ' : '' }}
            </span>
          </p>
        </li>
      </ul>
    </div>
  </section>
</template>
