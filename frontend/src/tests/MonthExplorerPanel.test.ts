import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import MonthExplorerPanel from '../features/runtime/MonthExplorerPanel.vue'

describe('MonthExplorerPanel', () => {
  it('renders empty placeholders for month runs, arcs, and factions', () => {
    const wrapper = mount(MonthExplorerPanel, {
      props: {
        monthRuns: [],
        memoryCount: 0,
        arcs: [],
        factions: [],
        characterName: 'Mira Talren',
      },
    })
    expect(wrapper.get('[data-testid="month-explorer"]').text()).toContain('Month explorer')
    expect(wrapper.text()).toContain('No month runs recorded yet.')
    expect(wrapper.text()).toContain('Mira Talren: 0 memory(ies)')
    expect(wrapper.text()).toContain('No arcs registered yet.')
    expect(wrapper.text()).toContain('No factions registered yet.')
  })

  it('lists month run status when present', () => {
    const wrapper = mount(MonthExplorerPanel, {
      props: {
        monthRuns: [
          {
            id: 'm1',
            world_id: 'w1',
            month_index: 1,
            status: 'completed',
            start_day_index: 0,
            end_day_index: 29,
          },
        ],
        memoryCount: 3,
        arcs: [
          {
            id: 'a1',
            world_id: 'w1',
            arc_key: 'ember-trail',
            title: 'Ember Trail',
            arc_scope: 'major',
            status: 'active',
            premise: 'A trail of ember',
            objective: 'Reach the vale',
            progress: '0.2',
            version: 0,
          },
        ],
        factions: [],
        characterName: 'Mira Talren',
      },
    })
    expect(wrapper.text()).toContain('Month 1')
    expect(wrapper.text()).toContain('completed')
    expect(wrapper.text()).toContain('Ember Trail')
    expect(wrapper.text()).toContain('Mira Talren: 3 memory(ies)')
  })
})
