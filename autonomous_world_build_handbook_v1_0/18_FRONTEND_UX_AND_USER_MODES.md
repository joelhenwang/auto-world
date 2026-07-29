# Frontend UX, Visual-Novel Presentation, and User Modes

**Version:** 1.0  
**Status:** Normative client specification  
**Primary owners:** `frontend`, design system, generated API client  
**Required reading:** `02`, `04`, `17`, `22`, and the active stage document

---

## 1. Purpose

This document defines the Vue 3 client architecture, navigation, state management, live updates, watcher/director/deity/player modes, perspective filtering, timeline and visual-novel presentation, map and encyclopedia views, operations UI, accessibility, error handling, and frontend testing.

The frontend displays canonical projections. It is not a second simulation engine.

---

## 2. Technology baseline

```text
Vue 3
TypeScript strict
Vite
Composition API with <script setup lang="ts">
Vue Router
Pinia for client/session/UI state
TanStack Query for server-state caching where appropriate
Generated API types/client from OpenAPI
Vitest
Vue Test Utils
Playwright for end-to-end tests
```

Vue provides first-class TypeScript support. Prefer Composition API for type inference and module boundaries.

Exact package versions belong in the frontend lockfile and version registry.

---

## 3. Frontend principles

1. Server is authoritative; do not derive canonical outcomes client-side.
2. Perspective filtering is enforced on the server and reflected visibly in the UI.
3. Role changes are explicit and audited where they alter control.
4. Live events update caches; REST remains the recovery source.
5. All long operations have visible state, retry/recovery guidance, and command IDs.
6. The user can pause and inspect without losing place.
7. Narrative presentation and developer diagnostics are separate modes.
8. Images enhance scenes but do not hide textual facts or block navigation.
9. Keyboard and screen-reader access are first-class.
10. Do not overwhelm the ordinary watcher with model/task internals.

---

## 4. Information architecture

Suggested routes:

```text
/
/world
/world/timeline
/world/visual-novel
/world/map
/world/encyclopedia
/world/arcs
/world/factions
/characters
/characters/:characterId
/characters/:characterId/diary
/characters/:characterId/memories
/scenes/:sceneId
/images
/control
/operations
/settings
```

The single-world product may redirect `/` to `/world/timeline` after setup.

---

## 5. Global shell

Desktop layout:

```text
┌──────────────────────────────────────────────────────────────┐
│ World title · fictional date/phase · runtime state · actions │
├─────────────┬──────────────────────────────────┬─────────────┤
│ Navigation  │ Main route content               │ Context     │
│             │                                  │ panel       │
├─────────────┴──────────────────────────────────┴─────────────┤
│ Live status / queued tasks / connection / perspective        │
└──────────────────────────────────────────────────────────────┘
```

Responsive layout collapses navigation and context panel into drawers.

Global header includes:

- current fictional date and phase;
- auto/manual state;
- running/paused/waiting/error state;
- selected role and perspective;
- pause or advance action if authorized;
- connection indicator;
- unresolved input badge.

---

## 6. User-mode selector

### 6.1 Watcher

- omniscient or voluntarily selected limited perspective;
- no canonical write controls;
- timeline, scenes, diaries, encyclopedia, map, and gallery;
- optional diagnostics toggle if authorized.

### 6.2 Director

Adds:

- propose event/hook;
- set high-level genre/tone pressure within allowed fields;
- suggest location/NPC/arc;
- review proposal status and validation failures.

Make clear that a Director command is a proposal, not an immediate fact.

### 6.3 Deity

Adds explicit high-impact command palette. Every form shows:

- affected entities;
- expected canonical effects;
- inconsistency risk;
- required justification;
- whether command is additive, soft correction, or hard retcon;
- confirmation for destructive operations.

Never provide a raw database editor.

### 6.4 Player

The user selects one eligible character. UI changes to:

- character-limited map/encyclopedia/timeline;
- current perception and known state;
- action composer when input is required;
- no access to other characters’ private tabs;
- clear banner that submitted actions are attempts.

Switching away from player control occurs at a safe boundary. The UI cannot restore human ignorance after omniscient viewing; it can only enforce display perspective.

---

## 7. Timeline view

### 7.1 Event card

Shows:

- fictional timestamp;
- event type and importance;
- location;
- participants as visible to perspective;
- canonical or perspective summary;
- selected image/placeholder;
- scene/dialogue expansion;
- source arc/hook tags when permitted;
- state changes in a collapsible facts section;
- perspective uncertainty markers;
- debug provenance only in diagnostics mode.

### 7.2 Filters

- character;
- location;
- arc;
- event type;
- generation;
- importance;
- image availability;
- date range;
- perspective.

Filters sync to URL query parameters for shareable local links and browser navigation.

### 7.3 Infinite/cursor loading

Use API cursors. Preserve scroll anchor when older events load or a late image appears. New live events display a “new events” affordance rather than jumping the user while reading history.

---

## 8. Visual-novel view

### 8.1 Scene presentation

- reusable background;
- character portraits/sprites with expression/outfit variants;
- dialogue and action beats;
- optional event CG;
- scene progress/beat indicator;
- auto-play with adjustable delay;
- manual next/previous;
- transcript drawer;
- accessibility transcript.

### 8.2 Source truth

The view consumes a `VisualNovelSceneProjection` from the API containing:

- scene ID;
- ordered beats;
- speaker/actor IDs;
- visible text;
- asset references;
- perspective;
- committed event IDs.

It does not parse raw narration to infer speakers or effects.

### 8.3 Missing images

Use:

- location colour/gradient fallback;
- character initials/silhouette;
- text-first layout;
- queued indicator.

The scene remains fully readable.

### 8.4 Late image arrival

Update asset in place without resetting current beat. Provide a subtle notification and gallery entry.

---

## 9. Character views

### 9.1 Overview

- portrait/reference;
- public or omniscient card fields;
- current location/state;
- role/focus level;
- age/generation;
- current activity;
- visible injuries;
- recent significant events.

### 9.2 Tabs

```text
Overview
Timeline
Stats & Skills
Goals & Plans
Relationships
Memories
Diary
Inventory
Magic
Images
History/Versions   # authorized debug/deity
```

Server perspective controls tab availability and fields.

### 9.3 Relationships visualization

Show directional relationships only when authorized. In player perspective, show the controlled character’s feelings and uncertain perceived reciprocity, not target truth.

Use accessible tables alongside any graph visualization.

### 9.4 Memory inspector

Authorized view shows:

- memory type/content;
- salience/confidence;
- source observations;
- involved entities;
- retrieval metadata;
- embedding status;
- pin/rebuild actions.

Player view shows natural memories, not raw vector/debug internals unless explicitly allowed.

---

## 10. Map

### 10.1 Representation

- graph nodes and routes;
- optional geographic coordinates;
- region hierarchy;
- character positions;
- travel activities/progress;
- weather/faction overlays;
- discovered/unknown handling.

### 10.2 Perspective

Character perspective:

- undiscovered locations absent or vague;
- uncertain routes styled as uncertain;
- secret locations hidden;
- current location and known travel estimates shown;
- no omniscient enemy positions.

### 10.3 Accessibility

Provide a list/tree route representation with distances and connections. The graphical map cannot be the only way to navigate.

---

## 11. Encyclopedia

Categories:

- world and cosmology;
- regions and locations;
- species/cultures;
- magic;
- history;
- factions;
- notable characters;
- items;
- legends and rumours.

Every entry indicates epistemic status according to perspective:

```text
Known fact
Believed
Rumoured
Uncertain
Contradicted
Unknown
```

Omniscient mode may compare canonical fact and character beliefs. Player mode never receives hidden canonical text.

---

## 12. Control centre

### 12.1 Runtime controls

- start;
- pause mode;
- resume;
- advance one phase;
- auto mode;
- stop after phase/day;
- current task/scene;
- pending player input;
- quota status;
- degraded mode.

### 12.2 Director form

Structured fields with natural-language intent:

- proposal category;
- target entities/locations;
- intended horizon;
- urgency;
- constraints;
- private/public handling;
- optional text brief.

Display validation and resolution status.

### 12.3 Deity command palette

Use separate forms for each command type. Destructive commands require confirmation and show potential inconsistency warnings.

### 12.4 Player action composer

Offer:

- natural-language intent;
- optional action family;
- target selector limited to known entities;
- brief dialogue;
- fallback intention;
- current resources and perception;
- deadline/status.

Do not expose resolver effect fields.

---

## 13. Operations view

Protected route with:

- worker health;
- model profiles/capabilities;
- provider quota/budget;
- current task queues;
- active leases;
- dead-letter tasks;
- image queue;
- phase state machine;
- database migration/version status;
- consistency warnings;
- sanitized model-call diagnostics;
- manual reconcile/retry actions.

Use compact tables, filters, and detail drawers. Keep it separate from narrative experience.

---

## 14. State management

### 14.1 Server state

Use generated API client plus query cache for:

- world projections;
- timeline pages;
- character resources;
- map/encyclopedia;
- command status;
- operations data.

### 14.2 Client state

Pinia/local state for:

- selected role/perspective;
- layout and panel state;
- timeline filters;
- visual-novel playback settings;
- drafts not yet submitted;
- connection state;
- diagnostics preference.

Do not duplicate full canonical world state into a mutable Pinia store.

### 14.3 WebSocket integration

WebSocket events should invalidate/update targeted query caches by stable IDs. On gap or `RESYNC_REQUIRED`, refetch current projections.

Deduplicate using stream event ID/sequence.

---

## 15. Optimistic UI

Allowed:

- show a submitted command as pending;
- disable duplicate action submission;
- display a local draft;
- immediately update pause button state as “requesting.”

Not allowed:

- display attack as successful before commit;
- move a character on the map from an action proposal;
- show a relationship change before event projection;
- assume a deity command completed without terminal command status.

---

## 16. Error and degraded states

Every route distinguishes:

```text
loading
empty
stale/reconnecting
provider_degraded
permission_denied
not_found
recoverable_error
terminal_world_state
```

Error UI includes request/command ID for diagnostics, not stack traces.

When model provider is unavailable, read-only history remains usable. When images are unavailable, scenes remain text-first.

---

## 17. Accessibility

Minimum requirements:

- semantic HTML;
- full keyboard navigation;
- visible focus;
- skip links;
- screen-reader labels and live regions for meaningful runtime updates;
- reduced-motion preference;
- colour contrast meeting WCAG AA target;
- no information conveyed by colour alone;
- captions/alt text for generated images based on committed scene facts;
- transcript alternatives for visual-novel presentation;
- scalable text and responsive layout;
- confirmation that does not depend on pointer-only gestures.

Generated-image alt text must not reveal facts unavailable to the selected perspective.

---

## 18. Content display

- sanitize rendered Markdown/HTML;
- do not render arbitrary model HTML;
- escape dialogue by default;
- allow a narrow trusted formatting subset generated by backend rendering;
- no remote image URLs from model output;
- object URLs come from trusted API projection;
- external links require explicit safe-link handling.

---

## 19. Frontend repository structure

```text
frontend/src/
├── app/
│   ├── router/
│   ├── providers/
│   └── App.vue
├── api/
│   ├── generated/
│   ├── client.ts
│   └── websocket.ts
├── features/
│   ├── world-runtime/
│   ├── timeline/
│   ├── visual-novel/
│   ├── characters/
│   ├── map/
│   ├── encyclopedia/
│   ├── control/
│   ├── images/
│   └── operations/
├── components/
│   ├── ui/
│   └── domain/
├── stores/
├── composables/
├── styles/
├── types/
└── tests/
```

Feature modules do not directly call `fetch`; they use API/query services.

---

## 20. Testing

### Unit/component tests

- role selector;
- perspective labels;
- event card states;
- command pending/terminal states;
- player action validation;
- visual-novel beat navigation;
- image placeholder/late arrival;
- map list fallback;
- inaccessible controls hidden/disabled appropriately;
- WebSocket reducer/deduplication.

### Integration tests

Use mocked generated client and a deterministic WebSocket harness.

### End-to-end tests

1. load seeded world and timeline;
2. advance a phase and watch live updates;
3. switch to player mode and submit an action;
4. verify omniscient secrets disappear in player perspective;
5. pause/resume;
6. submit Director proposal;
7. run a deity override with audit confirmation;
8. reconnect WebSocket and replay missed event;
9. view image job complete later;
10. navigate entirely by keyboard.

### Visual regression

Use for stable layout components and visual-novel composition with deterministic placeholder assets. Do not require pixel-stable generated AI images.

### Accessibility tests

Automated accessibility checks plus keyboard/manual tests for critical flows.

---

## 21. Stage introduction map

| UX capability | First required stage |
|---|---:|
| Minimal runtime/timeline/debug view | 1 |
| Four-character timeline, player mode, map basics, diary | 2 |
| Encyclopedia, arcs/factions, richer control and quality views | 3 |
| Visual-novel assets, gallery, distributed operations | 4 |
| Generation timeline, genealogy, macro-time controls, endings | 5 |

---

## 22. Definition of done

The frontend is complete for a stage when:

- it uses generated API types;
- role and perspective state are visible and server-enforced;
- all long commands show durable status;
- live updates reconnect and resync safely;
- narrative history remains usable without images/models;
- player mode cannot reveal omniscient fields through cached data;
- canonical state is not optimistically invented;
- critical flows are keyboard accessible and tested;
- operations diagnostics are separated from the ordinary story experience.

---

## 23. Official references

- Vue TypeScript overview: <https://vuejs.org/guide/typescript/overview.html>
- Vue Composition API with TypeScript: <https://vuejs.org/guide/typescript/composition-api.html>
- Vue component fundamentals: <https://vuejs.org/guide/essentials/component-basics.html>
