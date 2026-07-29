import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import RuntimeHeader from '../features/runtime/RuntimeHeader.vue'

describe('RuntimeHeader', () => {
  it('shows fictional phase, runtime, connection, and emits controls', async () => {
    const wrapper = mount(RuntimeHeader, {
      props: {
        world: {
          id: 'world-1',
          slug: 'caldris',
          name: 'Caldris: Embervale',
          status: 'active',
          current_event_sequence: 3,
          version: 1,
        },
        clock: {
          world_id: 'world-1',
          generation_number: 1,
          year: 612,
          month: 1,
          day: 1,
          phase_name: 'morning',
          phase_ordinal: 2,
          absolute_day_index: 0,
          absolute_phase_index: 1,
          resolution_mode: 'detailed',
          version: 2,
        },
        runtimeState: 'idle',
        connectionState: 'live',
        busy: false,
      },
    })

    expect(wrapper.text()).toContain('Caldris: Embervale')
    expect(wrapper.text()).toContain('morning')
    expect(wrapper.text()).toContain('live')
    await wrapper.get('button').trigger('click')
    expect(wrapper.emitted('advance')).toHaveLength(1)
  })
})
