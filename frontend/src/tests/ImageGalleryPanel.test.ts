import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import {
  NONCANONICAL_ILLUSTRATION_BANNER,
  type GalleryItemRead,
} from '../api/stage4-types'
import ImageGalleryPanel from '../features/ops/ImageGalleryPanel.vue'

describe('ImageGalleryPanel', () => {
  it('always shows the noncanonical illustration banner', () => {
    const wrapper = mount(ImageGalleryPanel, {
      props: { items: [] },
    })
    const banner = wrapper.get('[data-testid="noncanonical-banner"]')
    expect(banner.text()).toBe(NONCANONICAL_ILLUSTRATION_BANNER)
    expect(banner.text()).toContain('noncanonical')
    expect(banner.text()).toContain('Illustrations only')
  })

  it('keeps the banner when gallery items are present', () => {
    const items: GalleryItemRead[] = [
      {
        id: 'g1',
        world_id: 'w1',
        image_job_id: 'j1',
        asset_object_id: 'a1',
        asset_class: 'scene_cg',
        display_status: 'auto_selected',
        is_canonical_illustration: false,
        qc_passed: true,
        caption: 'Bridge at dusk',
      },
    ]
    const wrapper = mount(ImageGalleryPanel, {
      props: { items },
    })
    expect(wrapper.get('[data-testid="noncanonical-banner"]').text()).toBe(
      NONCANONICAL_ILLUSTRATION_BANNER,
    )
    expect(wrapper.text()).toContain('Bridge at dusk')
    expect(wrapper.text()).toContain('illustration')
  })
})
