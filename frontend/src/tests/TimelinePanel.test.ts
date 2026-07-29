import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import TimelinePanel from '../features/runtime/TimelinePanel.vue'

describe('TimelinePanel', () => {
  it('keeps committed narration readable without an image', () => {
    const wrapper = mount(TimelinePanel, {
      props: {
        loading: false,
        characters: [
          {
            id: 'mira',
            name: 'Mira Talren',
            location_id: 'inn',
            life_status: 'alive',
            stamina: '82',
            energy: '74',
            pain: '0',
            stress: '12',
            active_activity_id: null,
            state_version: 1,
          },
        ],
        locations: [{ id: 'inn', name: 'The Embervale Inn' }],
        events: [
          {
            id: 'stream-1',
            world_id: 'world-1',
            sequence: 4,
            event_type: 'scene.committed',
            occurred_at: '2026-07-29T00:00:00Z',
            fictional_time: { phase_name: 'dawn' },
            payload: {
              canonical_summary: 'Mira and Dain share news at the inn.',
              character_ids: ['mira'],
              location_id: 'inn',
            },
            schema_version: '1',
            phase_run_id: 'phase-1',
            scene_id: 'scene-1',
            world_event_id: 'event-1',
            perspective_scope: 'world',
          },
        ],
      },
    })

    expect(wrapper.text()).toContain('Mira and Dain share news at the inn.')
    expect(wrapper.text()).toContain('Text-first scene')
    expect(wrapper.get('.scene-placeholder').attributes('aria-label')).toContain(
      'Image unavailable',
    )
    expect(wrapper.text()).toContain('All characters')
    expect(wrapper.text()).toContain('All locations')
  })
})
