import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import WorkerHealthPanel from '../features/ops/WorkerHealthPanel.vue'
import ImageQueuePanel from '../features/ops/ImageQueuePanel.vue'
import VisualProfilePanel from '../features/ops/VisualProfilePanel.vue'

describe('Stage 4 ops panels', () => {
  it('renders worker health empty placeholders', () => {
    const wrapper = mount(WorkerHealthPanel, {
      props: { health: { hosts: [], workers: [], models: [] } },
    })
    expect(wrapper.get('[data-testid="worker-health"]').text()).toContain('Worker health')
    expect(wrapper.text()).toContain('No hosts registered yet.')
    expect(wrapper.text()).toContain('No workers registered yet.')
    expect(wrapper.text()).toContain('No model health probes recorded.')
  })

  it('lists hosts and workers when provided', () => {
    const wrapper = mount(WorkerHealthPanel, {
      props: {
        health: {
          hosts: [
            {
              id: 'h1',
              host_key: 'halo-a',
              status: 'active',
              capabilities: ['llm', 'image'],
            },
          ],
          workers: [
            {
              id: 'w1',
              host_id: 'h1',
              worker_key: 'worker-1',
              status: 'active',
              capabilities: ['phase'],
            },
          ],
          models: [
            {
              model_key: 'local-qwen',
              role: 'character',
              status: 'ready',
              backend: 'vllm',
            },
          ],
        },
      },
    })
    expect(wrapper.text()).toContain('halo-a')
    expect(wrapper.text()).toContain('worker-1')
    expect(wrapper.text()).toContain('local-qwen')
  })

  it('renders image queue empty and populated states', () => {
    const empty = mount(ImageQueuePanel, { props: { jobs: [] } })
    expect(empty.get('[data-testid="image-queue"]').text()).toContain('Image queue')
    expect(empty.text()).toContain('No image jobs queued')

    const filled = mount(ImageQueuePanel, {
      props: {
        jobs: [
          {
            id: 'j1',
            world_id: 'w1',
            idempotency_key: 'img:1',
            asset_class: 'scene_cg',
            status: 'queued',
            priority: 50,
            attempt: 0,
            max_attempts: 3,
            workflow_version: 'stub_v1',
          },
        ],
      },
    })
    expect(filled.text()).toContain('scene_cg')
    expect(filled.text()).toContain('queued')
    expect(filled.text()).toContain('stub_v1')
  })

  it('renders visual profile management stub', () => {
    const empty = mount(VisualProfilePanel, { props: { profiles: [] } })
    expect(empty.get('[data-testid="visual-profiles"]').text()).toContain('Visual profiles')
    expect(empty.text()).toContain('No character or location visual profiles yet')

    const filled = mount(VisualProfilePanel, {
      props: {
        profiles: [
          {
            id: 'p1',
            world_id: 'w1',
            subject_type: 'character',
            subject_id: 'c1',
            subject_label: 'Mira Talren',
            profile_version: 2,
            status: 'active',
            reference_asset_ids: ['a1'],
            style_summary: 'Ember cloak, ash-grey braid',
          },
        ],
      },
    })
    expect(filled.text()).toContain('Mira Talren')
    expect(filled.text()).toContain('v2')
    expect(filled.text()).toContain('Ember cloak, ash-grey braid')
  })
})
