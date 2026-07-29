<script setup lang="ts">
import { computed } from 'vue'

import type { MapStateRead } from '../../api/client'

const props = defineProps<{
  map: MapStateRead
  characterNames: Record<string, string>
}>()

const locationNames = computed(() => {
  const names: Record<string, string> = {}
  for (const location of props.map.locations) {
    names[location.id] = location.name
  }
  return names
})

function place(id: string | null | undefined): string {
  if (!id) return 'unknown'
  return locationNames.value[id] ?? id.slice(0, 8)
}

function actor(id: string): string {
  return props.characterNames[id] ?? id.slice(0, 8)
}

function progressLabel(value: number | string): string {
  const numeric = Number(value)
  if (Number.isNaN(numeric)) return String(value)
  return `${Math.round(numeric * 100)}%`
}
</script>

<template>
  <section class="panel map-panel" aria-labelledby="map-title">
    <div class="panel-heading">
      <div>
        <p class="eyebrow">World geography</p>
        <h2 id="map-title">Map &amp; routes</h2>
      </div>
      <span class="count">{{ map.locations.length }} places</span>
    </div>

    <div class="map-body">
      <section aria-labelledby="locations-heading">
        <h3 id="locations-heading">Locations</h3>
        <p v-if="map.locations.length === 0" class="empty-state compact">
          Map endpoints unavailable or empty.
        </p>
        <ul v-else class="detail-list">
          <li v-for="location in map.locations" :key="location.id">
            <strong>{{ location.name }}</strong>
            <span class="muted">
              {{ location.region || 'region unknown' }}
              <template v-if="location.character_ids?.length">
                ·
                {{
                  location.character_ids
                    .map((id) => actor(id))
                    .join(', ')
                }}
              </template>
            </span>
          </li>
        </ul>
      </section>

      <section aria-labelledby="routes-heading">
        <h3 id="routes-heading">Routes</h3>
        <p v-if="map.routes.length === 0" class="empty-state compact">
          No routes listed.
        </p>
        <ul v-else class="detail-list">
          <li v-for="route in map.routes" :key="route.id">
            <strong>
              {{ place(route.origin_location_id) }}
              →
              {{ place(route.destination_location_id) }}
            </strong>
            <span class="muted">
              {{ route.distance_units ?? '—' }} units ·
              {{ route.base_duration_phases ?? '—' }} phases
            </span>
          </li>
        </ul>
      </section>

      <section aria-labelledby="travel-heading">
        <h3 id="travel-heading">Current travel</h3>
        <p v-if="map.travel.length === 0" class="empty-state compact">
          No active travel.
        </p>
        <ul v-else class="detail-list">
          <li v-for="trip in map.travel" :key="trip.activity_id">
            <strong>{{ actor(trip.owner_entity_id) }}</strong>
            <span class="muted">
              {{ place(trip.origin_location_id) }}
              →
              {{ place(trip.destination_location_id) }}
              · {{ progressLabel(trip.progress) }} · {{ trip.status }}
            </span>
          </li>
        </ul>
      </section>
    </div>
  </section>
</template>
