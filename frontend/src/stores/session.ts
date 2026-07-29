import { defineStore } from 'pinia'

import type { PlayerControlRead } from '../api/client'

export type UserMode = 'watcher' | 'player'

export const useSessionStore = defineStore('session', {
  state: () => ({
    mode: 'watcher' as UserMode,
    selectedCharacterId: undefined as string | undefined,
    control: undefined as PlayerControlRead | undefined,
    controllerId: 'local-player',
  }),
  getters: {
    observerId: (state): string | undefined =>
      state.mode === 'player' ? state.selectedCharacterId : undefined,
  },
  actions: {
    enterPlayer(characterId: string, control: PlayerControlRead) {
      this.mode = 'player'
      this.selectedCharacterId = characterId
      this.control = control
    },
    enterWatcher() {
      this.mode = 'watcher'
      this.selectedCharacterId = undefined
      this.control = undefined
    },
  },
})
