<script setup lang="ts">
import { computed, ref } from 'vue'

import type { CharacterSummaryRead } from '../../api/client'
import type { ActionDraft } from './types'

const props = defineProps<{
  character: CharacterSummaryRead
  characters: CharacterSummaryRead[]
  busy: boolean
}>()

const emit = defineEmits<{
  submit: [draft: ActionDraft]
}>()

const actionFamily = ref('communicate')
const description = ref('')
const utterance = ref('')
const targetId = ref('')
const canSubmit = computed(() => description.value.trim().length > 0 && !props.busy)
const possibleTargets = computed(() =>
  props.characters.filter((character) => character.id !== props.character.id),
)

function submit(): void {
  if (!canSubmit.value) {
    return
  }
  emit('submit', {
    actionFamily: actionFamily.value,
    description: description.value.trim(),
    utterance: utterance.value.trim() || undefined,
    targetEntityIds: targetId.value ? [targetId.value] : [],
  })
  description.value = ''
  utterance.value = ''
}
</script>

<template>
  <section class="panel composer" aria-labelledby="composer-title">
    <div class="panel-heading">
      <div>
        <p class="eyebrow">Player mode · {{ character.name }}</p>
        <h2 id="composer-title">Propose an action</h2>
      </div>
      <span class="attempt-label">Attempt, not outcome</span>
    </div>
    <form @submit.prevent="submit">
      <label>
        Action family
        <select v-model="actionFamily">
          <option value="communicate">Communicate</option>
          <option value="observe">Observe</option>
          <option value="rest">Rest</option>
          <option value="wait">Wait</option>
          <option value="move">Move</option>
          <option value="socialize">Socialize</option>
          <option value="interact_environment">Interact with environment</option>
          <option value="continue_activity">Continue activity</option>
        </select>
      </label>
      <label>
        Intent
        <textarea
          v-model="description"
          required
          maxlength="2000"
          placeholder="What does the character try to do?"
        ></textarea>
      </label>
      <div class="form-row">
        <label>
          Known target
          <select v-model="targetId">
            <option value="">No specific character</option>
            <option
              v-for="target in possibleTargets"
              :key="target.id"
              :value="target.id"
            >
              {{ target.name }}
            </option>
          </select>
        </label>
        <label>
          Optional dialogue
          <input
            v-model="utterance"
            maxlength="1000"
            placeholder="What do they say?"
          />
        </label>
      </div>
      <button type="submit" :disabled="!canSubmit">Submit attempt</button>
    </form>
  </section>
</template>
