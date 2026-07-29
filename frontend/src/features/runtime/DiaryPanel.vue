<script setup lang="ts">
import type { DiaryEntryRead, SummaryRead } from '../../api/client'

defineProps<{
  characterName?: string
  diaries: DiaryEntryRead[]
  summaries: SummaryRead[]
  loading?: boolean
}>()
</script>

<template>
  <section class="panel diary-panel" aria-labelledby="diary-title">
    <div class="panel-heading">
      <div>
        <p class="eyebrow">Daily consolidation</p>
        <h2 id="diary-title">
          Diary{{ characterName ? ` · ${characterName}` : '' }}
        </h2>
      </div>
      <span class="count">{{ diaries.length }} entries</span>
    </div>

    <p v-if="loading" class="empty-state">Loading diary…</p>
    <p v-else-if="!characterName" class="empty-state">
      Select a character to read their diary and daily summaries.
    </p>
    <div v-else class="diary-body">
      <section aria-labelledby="summaries-heading">
        <h3 id="summaries-heading">Summaries</h3>
        <p v-if="summaries.length === 0" class="empty-state compact">
          No daily summaries yet.
        </p>
        <article v-for="summary in summaries" :key="summary.id" class="diary-card">
          <div class="event-meta">
            <span>{{ summary.summary_type }}</span>
            <span>
              Phases {{ summary.start_phase_index }}–{{ summary.end_phase_index }}
            </span>
          </div>
          <p>{{ summary.content }}</p>
        </article>
      </section>

      <section aria-labelledby="entries-heading">
        <h3 id="entries-heading">Diary entries</h3>
        <p v-if="diaries.length === 0" class="empty-state compact">
          No diary entries yet.
        </p>
        <article v-for="entry in diaries" :key="entry.id" class="diary-card">
          <div class="event-meta">
            <span>Day {{ entry.day_index + 1 }}</span>
          </div>
          <p>{{ entry.content }}</p>
        </article>
      </section>
    </div>
  </section>
</template>
