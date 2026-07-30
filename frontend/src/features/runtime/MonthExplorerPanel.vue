<script setup lang="ts">
import type { ArcRead, FactionRead, MonthRunRead } from '../../api/stage3-types'

defineProps<{
  monthRuns: MonthRunRead[]
  memoryCount: number
  arcs: ArcRead[]
  factions: FactionRead[]
  characterName?: string
}>()
</script>

<template>
  <section
    class="panel month-explorer-panel"
    data-testid="month-explorer"
    aria-labelledby="month-explorer-title"
  >
    <div class="panel-heading">
      <div>
        <p class="eyebrow">Thirty-day run</p>
        <h2 id="month-explorer-title">Month explorer</h2>
      </div>
      <span class="count">{{ monthRuns.length }} month run(s)</span>
    </div>

    <div class="director-body">
      <section aria-labelledby="month-runs-heading">
        <h3 id="month-runs-heading">Month runs</h3>
        <p v-if="monthRuns.length === 0" class="empty-state compact">
          No month runs recorded yet.
        </p>
        <ul v-else class="detail-list">
          <li v-for="run in monthRuns" :key="run.id">
            <strong>Month {{ run.month_index }}</strong>
            <span class="muted">
              {{ run.status }} · days {{ run.start_day_index }}–{{ run.end_day_index }}
            </span>
          </li>
        </ul>
      </section>

      <section aria-labelledby="memories-heading">
        <h3 id="memories-heading">Long-term memories</h3>
        <p class="empty-state compact">
          <template v-if="characterName">
            {{ characterName }}: {{ memoryCount }} memory(ies)
          </template>
          <template v-else>
            Select a character to load memory counts.
          </template>
        </p>
      </section>

      <section aria-labelledby="arcs-heading">
        <h3 id="arcs-heading">Arcs</h3>
        <p v-if="arcs.length === 0" class="empty-state compact">
          No arcs registered yet.
        </p>
        <ul v-else class="detail-list">
          <li v-for="arc in arcs" :key="arc.id">
            <strong>{{ arc.title }}</strong>
            <span class="muted">
              {{ arc.status }} · {{ arc.arc_scope }} · {{ arc.arc_key }}
            </span>
          </li>
        </ul>
      </section>

      <section aria-labelledby="factions-heading">
        <h3 id="factions-heading">Factions</h3>
        <p v-if="factions.length === 0" class="empty-state compact">
          No factions registered yet.
        </p>
        <ul v-else class="detail-list">
          <li v-for="faction in factions" :key="faction.id">
            <strong>{{ faction.name }}</strong>
            <span class="muted">
              {{ faction.status }} · {{ faction.faction_type }} · {{ faction.faction_key }}
            </span>
          </li>
        </ul>
      </section>
    </div>
  </section>
</template>
