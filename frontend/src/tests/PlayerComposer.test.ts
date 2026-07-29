import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import type { CharacterSummaryRead } from '../api/client'
import PlayerComposer from '../features/runtime/PlayerComposer.vue'

const mira: CharacterSummaryRead = {
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
}

const dain: CharacterSummaryRead = {
  ...mira,
  id: 'dain',
  name: 'Dain Arcen',
}

describe('PlayerComposer', () => {
  it('labels actions as attempts and emits only after an intent is entered', async () => {
    const wrapper = mount(PlayerComposer, {
      props: {
        character: mira,
        characters: [mira, dain],
        busy: false,
      },
    })

    const submit = wrapper.get<HTMLButtonElement>('button[type="submit"]')
    expect(wrapper.text()).toContain('Attempt, not outcome')
    expect(submit.element.disabled).toBe(true)

    await wrapper.get('textarea').setValue('Ask Dain whether the bridge is open.')
    await wrapper.findAll('select')[1]!.setValue('dain')
    await wrapper.get('input').setValue('Is the east bridge open?')
    await wrapper.get('form').trigger('submit')

    expect(wrapper.emitted('submit')?.[0]?.[0]).toEqual({
      actionFamily: 'communicate',
      description: 'Ask Dain whether the bridge is open.',
      utterance: 'Is the east bridge open?',
      targetEntityIds: ['dain'],
    })
  })
})
