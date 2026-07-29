import { defineStore } from 'pinia'

import type { PlayerControlRead } from '../api/client'

export type UserMode = 'watcher' | 'director' | 'player'

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
    /** Watcher/director may see Director metrics; player must not. */
    canViewDirector: (state): boolean =>
      state.mode === 'watcher' || state.mode === 'director',
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
    enterDirector() {
      this.mode = 'director'
      this.selectedCharacterId = undefined
      this.control = undefined
    },
  },
})
