<script setup lang="ts">
import {
  NONCANONICAL_ILLUSTRATION_BANNER,
  type GalleryItemRead,
} from '../../api/stage4-types'

withDefaults(
  defineProps<{
    items?: GalleryItemRead[]
  }>(),
  {
    items: () => [],
  },
)
</script>

<template>
  <section
    class="panel image-gallery-panel"
    data-testid="image-gallery"
    aria-labelledby="image-gallery-title"
  >
    <div class="panel-heading">
      <div>
        <p class="eyebrow">Visual novel</p>
        <h2 id="image-gallery-title">Image gallery</h2>
      </div>
      <span class="count">{{ items.length }} item(s)</span>
    </div>

    <p
      class="noncanonical-banner"
      data-testid="noncanonical-banner"
      role="note"
    >
      {{ NONCANONICAL_ILLUSTRATION_BANNER }}
    </p>

    <p v-if="items.length === 0" class="empty-state">
      No gallery illustrations yet. Generated images remain illustrative only.
    </p>
    <ul v-else class="gallery-grid" aria-label="Gallery illustrations">
      <li v-for="item in items" :key="item.id" class="gallery-tile">
        <div class="gallery-preview" aria-hidden="true">
          <template v-if="item.preview_url">
            <img :src="item.preview_url" :alt="item.caption ?? item.asset_class" />
          </template>
          <template v-else>
            <span>{{ item.asset_class.slice(0, 1).toUpperCase() }}</span>
            <small>{{ item.asset_class }}</small>
          </template>
        </div>
        <div class="gallery-meta">
          <strong>{{ item.caption ?? item.asset_class }}</strong>
          <span class="muted">
            {{ item.display_status }}
            · {{ item.qc_passed ? 'qc pass' : 'qc pending' }}
            · illustration
          </span>
        </div>
      </li>
    </ul>
  </section>
</template>
