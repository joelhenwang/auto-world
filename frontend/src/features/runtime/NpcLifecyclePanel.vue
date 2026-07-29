<script setup lang="ts">
import type { NpcLifecycleRead } from '../../api/client'

defineProps<{
  npcs: NpcLifecycleRead[]
}>()
</script>

<template>
  <section class="panel npc-panel" aria-labelledby="npc-title">
    <div class="panel-heading">
      <div>
        <p class="eyebrow">Bounded cast</p>
        <h2 id="npc-title">NPC lifecycle</h2>
      </div>
      <span class="count">{{ npcs.length }}</span>
    </div>

    <p v-if="npcs.length === 0" class="empty-state">
      No temporary NPCs registered yet.
    </p>
    <ul v-else class="detail-list padded">
      <li v-for="npc in npcs" :key="npc.character_id">
        <strong>{{ npc.display_name }}</strong>
        <span class="muted">
          {{ npc.lifecycle_status }}
          <template v-if="npc.role_tags?.length">
            · {{ npc.role_tags.join(', ') }}
          </template>
          <template v-if="npc.activated_phase_index != null">
            · active from phase {{ npc.activated_phase_index }}
          </template>
        </span>
        <p v-if="npc.archive_summary" class="npc-summary">
          {{ npc.archive_summary }}
        </p>
      </li>
    </ul>
  </section>
</template>
