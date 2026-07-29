<script setup lang="ts">
import type { CharacterSummaryRead } from '../../api/client'
import type { UserMode } from '../../stores/session'

defineProps<{
  characters: CharacterSummaryRead[]
  mode: UserMode
  selectedCharacterId?: string
  busy: boolean
}>()

defineEmits<{
  selectPlayer: [characterId: string]
  selectWatcher: []
}>()

function stat(value: number | string): number {
  return Math.max(0, Math.min(100, Number(value)))
}
</script>

<template>
  <section class="panel character-panel" aria-labelledby="characters-title">
    <div class="panel-heading">
      <div>
        <p class="eyebrow">Perspective</p>
        <h2 id="characters-title">Characters</h2>
      </div>
      <button
        type="button"
        class="mode-button"
        :class="{ active: mode === 'watcher' }"
        :disabled="busy"
        @click="$emit('selectWatcher')"
      >
        Watcher
      </button>
    </div>

    <p v-if="characters.length === 0" class="empty-state">Loading characters…</p>
    <div v-else class="character-list">
      <article
        v-for="character in characters"
        :key="character.id"
        class="character-card"
        :class="{ selected: character.id === selectedCharacterId }"
      >
        <div class="portrait" aria-hidden="true">
          {{ character.name.split(' ').map((part) => part[0]).join('') }}
        </div>
        <div class="character-copy">
          <div class="character-title">
            <div>
              <h3>{{ character.name }}</h3>
              <p>{{ character.life_status }} · state {{ character.state_version }}</p>
            </div>
            <button
              type="button"
              class="mode-button"
              :class="{ active: character.id === selectedCharacterId }"
              :disabled="busy"
              :aria-label="`Play as ${character.name}`"
              @click="$emit('selectPlayer', character.id)"
            >
              Player
            </button>
          </div>
          <dl>
            <div>
              <dt>Stamina</dt>
              <dd>
                <progress :value="stat(character.stamina)" max="100"></progress>
                {{ character.stamina }}
              </dd>
            </div>
            <div>
              <dt>Energy</dt>
              <dd>
                <progress :value="stat(character.energy)" max="100"></progress>
                {{ character.energy }}
              </dd>
            </div>
            <div>
              <dt>Stress</dt>
              <dd>{{ character.stress }}</dd>
            </div>
          </dl>
        </div>
      </article>
    </div>
  </section>
</template>
