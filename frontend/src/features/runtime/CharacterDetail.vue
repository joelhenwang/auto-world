<script setup lang="ts">
import type {
  CommitmentRead,
  GoalRead,
  PlanRead,
  RelationshipRead,
} from '../../api/client'

defineProps<{
  goals: GoalRead[]
  plans: PlanRead[]
  commitments: CommitmentRead[]
  relationships: RelationshipRead[]
  characterNames: Record<string, string>
}>()

function label(id: string, names: Record<string, string>): string {
  return names[id] ?? id.slice(0, 8)
}

function metric(value: number | string): string {
  const numeric = Number(value)
  if (Number.isNaN(numeric)) return String(value)
  return numeric.toFixed(2)
}
</script>

<template>
  <div class="character-detail" data-testid="character-detail">
    <section aria-labelledby="goals-title">
      <h3 id="goals-title">Goals &amp; plans</h3>
      <p v-if="goals.length === 0 && plans.length === 0" class="empty-state compact">
        No goals or plans loaded yet.
      </p>
      <ul v-else class="detail-list">
        <li v-for="goal in goals" :key="goal.id">
          <strong>{{ goal.description }}</strong>
          <span class="muted">{{ goal.status }} · {{ goal.category }}</span>
        </li>
        <li v-for="plan in plans" :key="plan.id">
          <strong>{{ plan.title }}</strong>
          <span class="muted">
            {{ plan.status }}{{ plan.is_primary ? ' · primary' : '' }}
          </span>
        </li>
      </ul>
      <template v-if="commitments.length">
        <h4>Commitments</h4>
        <ul class="detail-list">
          <li v-for="item in commitments" :key="item.id">
            <strong>{{ item.description }}</strong>
            <span class="muted">
              {{ label(item.debtor_character_id, characterNames) }} →
              {{ label(item.beneficiary_character_id, characterNames) }} ·
              {{ item.status }}
            </span>
          </li>
        </ul>
      </template>
    </section>

    <section aria-labelledby="relationships-title">
      <h3 id="relationships-title">Relationships</h3>
      <p v-if="relationships.length === 0" class="empty-state compact">
        No directional relationships available.
      </p>
      <table v-else class="relationship-table">
        <thead>
          <tr>
            <th scope="col">Toward</th>
            <th scope="col">Trust</th>
            <th scope="col">Affection</th>
            <th scope="col">Respect</th>
            <th scope="col">Fear</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="edge in relationships" :key="`${edge.source_character_id}-${edge.target_character_id}`">
            <td>{{ label(edge.target_character_id, characterNames) }}</td>
            <td>{{ metric(edge.trust) }}</td>
            <td>{{ metric(edge.affection) }}</td>
            <td>{{ metric(edge.respect) }}</td>
            <td>{{ metric(edge.fear) }}</td>
          </tr>
        </tbody>
      </table>
    </section>
  </div>
</template>
