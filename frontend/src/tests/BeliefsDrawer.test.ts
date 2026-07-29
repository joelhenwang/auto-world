import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import BeliefsDrawer from '../features/runtime/BeliefsDrawer.vue'

const sampleBeliefs = [
  {
    id: 'belief-1',
    character_id: 'mira',
    proposition_key: 'bridge_open',
    belief_text: 'The east bridge is open.',
    confidence: 0.8,
    status: 'active',
    evidence: [{ source_kind: 'observation', source_id: 'obs-1' }],
  },
]

describe('BeliefsDrawer', () => {
  it('hides beliefs in player mode when unauthorized', () => {
    const wrapper = mount(BeliefsDrawer, {
      props: {
        beliefs: sampleBeliefs,
        mode: 'player',
        authorized: false,
        characterName: 'Mira Talren',
      },
    })

    expect(wrapper.find('[data-testid="beliefs-drawer"]').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('The east bridge is open.')
  })

  it('shows beliefs for watcher mode when authorized', async () => {
    const wrapper = mount(BeliefsDrawer, {
      props: {
        beliefs: sampleBeliefs,
        mode: 'watcher',
        authorized: true,
        characterName: 'Mira Talren',
      },
    })

    expect(wrapper.find('[data-testid="beliefs-drawer"]').exists()).toBe(true)
    await wrapper.get('.drawer-toggle').trigger('click')
    expect(wrapper.text()).toContain('The east bridge is open.')
    expect(wrapper.text()).toContain('observation')
  })

  it('shows own beliefs in player mode when authorized', async () => {
    const wrapper = mount(BeliefsDrawer, {
      props: {
        beliefs: sampleBeliefs,
        mode: 'player',
        authorized: true,
        characterName: 'Mira Talren',
      },
    })

    expect(wrapper.find('[data-testid="beliefs-drawer"]').exists()).toBe(true)
    await wrapper.get('.drawer-toggle').trigger('click')
    expect(wrapper.text()).toContain('The east bridge is open.')
  })
})
