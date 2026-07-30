<script setup lang="ts">
import type { VisualProfileRead } from '../../api/stage4-types'

withDefaults(
  defineProps<{
    profiles?: VisualProfileRead[]
  }>(),
  {
    profiles: () => [],
  },
)

function subjectLabel(profile: VisualProfileRead): string {
  return profile.subject_label ?? `${profile.subject_type} ${profile.subject_id.slice(0, 8)}`
}
</script>

<template>
  <section
    class="panel visual-profile-panel"
    data-testid="visual-profiles"
    aria-labelledby="visual-profiles-title"
  >
    <div class="panel-heading">
      <div>
        <p class="eyebrow">Continuity refs</p>
        <h2 id="visual-profiles-title">Visual profiles</h2>
      </div>
      <span class="count">{{ profiles.length }} profile(s)</span>
    </div>

    <p v-if="profiles.length === 0" class="empty-state">
      No character or location visual profiles yet. Management stubs await S4-API-001.
    </p>
    <ul v-else class="detail-list padded">
      <li v-for="profile in profiles" :key="profile.id">
        <strong>{{ subjectLabel(profile) }}</strong>
        <span class="muted">
          {{ profile.subject_type }} · v{{ profile.profile_version }} ·
          {{ profile.status }} · {{ profile.reference_asset_ids.length }} ref(s)
        </span>
        <p v-if="profile.style_summary" class="npc-summary">
          {{ profile.style_summary }}
        </p>
      </li>
    </ul>
  </section>
</template>
