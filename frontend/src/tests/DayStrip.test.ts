import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import DayStrip from '../features/runtime/DayStrip.vue'

describe('DayStrip', () => {
  it('renders ten phases and day N/7 run progress', () => {
    const wrapper = mount(DayStrip, {
      props: {
        clock: {
          world_id: 'world-1',
          generation_number: 1,
          year: 612,
          month: 1,
          day: 3,
          phase_name: 'afternoon',
          phase_ordinal: 5,
          absolute_day_index: 2,
          absolute_phase_index: 24,
          resolution_mode: 'detailed',
          version: 1,
        },
        progress: null,
      },
    })

    expect(wrapper.text()).toContain('Day 3/7')
    expect(wrapper.findAll('.phase-chip')).toHaveLength(10)
    expect(wrapper.get('[data-state="current"]').text()).toContain('afternoon')
    expect(wrapper.get('[data-testid="run-progress"]').text()).toContain('Phase 5')
  })

  it('prefers explicit run progress day_of_run when present', () => {
    const wrapper = mount(DayStrip, {
      props: {
        clock: {
          world_id: 'world-1',
          generation_number: 1,
          year: 612,
          month: 1,
          day: 1,
          phase_name: 'dawn',
          phase_ordinal: 1,
          absolute_day_index: 0,
          absolute_phase_index: 0,
          resolution_mode: 'detailed',
          version: 1,
        },
        progress: {
          world_id: 'world-1',
          day_index: 4,
          day_of_run: 5,
          total_days: 7,
          phase_name: 'dusk',
          phase_ordinal: 7,
        },
      },
    })

    expect(wrapper.text()).toContain('Day 5/7')
    expect(wrapper.get('[data-state="current"]').text()).toContain('dusk')
  })
})
