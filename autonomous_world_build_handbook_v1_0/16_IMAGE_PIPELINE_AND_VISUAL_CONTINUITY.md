# Image Pipeline and Visual Continuity

**Version:** 1.0  
**Status:** Normative Stage 4 specification; earlier stages may create placeholder jobs  
**Primary owners:** `application.images`, `infrastructure.comfyui`, `domain.visuals`, frontend gallery  
**Required reading:** `04`, `06`, `09`, `14`, `15`, `18`, `22`, `29`

---

## 1. Purpose

This document defines when committed events deserve images, how visual assets are versioned, how ComfyUI workflows are submitted and monitored, how character/location continuity is maintained, how retries and quality checks work, and how image failure remains isolated from canonical simulation.

Images are illustrations of canon. They never create canon.

---

## 2. Core rules

1. Generate from committed scenes/events, never unresolved action proposals.
2. Image generation is asynchronous and never blocks the next phase.
3. A visual error does not change world state.
4. Character appearance, outfit, age, injuries, and transformations are versioned.
5. Every image records model, workflow, node-pack, LoRA/reference, seed, and source-event provenance.
6. The same event may have several image generations; one may be selected as the displayed asset.
7. Reusable visual-novel assets are preferred over a new full illustration for every dialogue line.
8. Content classification happens before job submission.
9. ComfyUI is behind an internal adapter; application code does not depend directly on arbitrary workflow node IDs.
10. Third-party custom nodes are pinned, reviewed, and treated as code execution dependencies.

---

## 3. Asset classes

### 3.1 Reusable assets

```text
CHARACTER_REFERENCE_SHEET
CHARACTER_PORTRAIT
CHARACTER_EXPRESSION
OUTFIT_REFERENCE
LOCATION_BACKGROUND
ITEM_REFERENCE
FACTION_SYMBOL
MAP_ILLUSTRATION
```

These support visual-novel rendering without generating a new scene image for each beat.

### 3.2 Event assets

```text
EVENT_CG
COMBAT_CG
RELATIONSHIP_MILESTONE_CG
DISCOVERY_CG
TRANSFORMATION_CG
COMEDIC_CG
ARC_KEY_ART
GENERATION_PORTRAIT
ENDING_CG
```

### 3.3 Operational assets

```text
THUMBNAIL
PREVIEW
CONTACT_SHEET
MASK
CONTROL_REFERENCE
QUALITY_CHECK_CROP
```

Operational assets are not normally shown in the timeline.

---

## 4. Image eligibility

A committed scene receives a deterministic `visual_score`:

```text
visual_score =
    0.25 × narrative_significance
  + 0.20 × visual_novelty
  + 0.20 × emotional_intensity
  + 0.15 × focus_character_importance
  + 0.10 × action_intensity
  + 0.10 × user_preference
```

All components use `0..1` and are sourced from resolution/event metadata.

### 4.1 Default policy

```yaml
target_event_cgs_per_detailed_day: 4
hard_cap_event_cgs_per_detailed_day: 8
max_event_cgs_per_scene: 1
minimum_visual_score: 0.58
always_eligible_tags:
  - MAJOR_ARC_MILESTONE
  - TRANSFORMATION
  - GENERATION_TRANSITION
  - ENDING
never_auto_generate_tags:
  - CONTENT_REVIEW_REQUIRED
  - GRAPHIC_VIOLENCE
  - SEXUAL_CONTENT
```

Reusable backgrounds and portraits are not counted as new event CGs once generated.

### 4.2 User overrides

The user may:

- force an image for a committed scene;
- raise/lower job priority;
- cancel a pending job;
- regenerate with a new seed or approved prompt revision;
- select a displayed generation;
- hide/delete a displayed asset while retaining audit metadata according to policy.

The user cannot cause an unresolved proposed event to become canon by generating it.

---

## 5. Visual state model

### 5.1 Character visual identity

```text
CharacterVisualProfile
├── character_id
├── profile_version
├── valid_from_event_id
├── apparent_age
├── body_proportions
├── height_reference
├── face_description
├── skin_description
├── hair_description
├── eye_description
├── species_features
├── stable_distinguishing_features
├── visual_negative_constraints
├── canonical_palette?
├── reference_asset_ids
└── supersedes_profile_id?
```

### 5.2 Outfit state

```text
OutfitVersion
├── outfit_version_id
├── character_id
├── name
├── garment_parts
├── accessories
├── colours/materials
├── condition
├── weather suitability
├── reference_asset_ids
├── valid_from_event_id
└── valid_to_event_id?
```

Current outfit belongs to `CharacterState` and changes only through events or defined routine transitions.

### 5.3 Visual injuries and transformations

The image specification receives active visible injuries and conditions. It must distinguish:

- visible now;
- hidden under clothing;
- healed scar;
- nonvisual internal injury;
- magical transformation.

A newly generated accidental scar is not adopted. A canonical scar requires an injury/appearance event and visual-profile update.

### 5.4 Location visual profile

```text
LocationVisualProfile
├── location_id
├── profile_version
├── architecture
├── layout anchors
├── materials
├── palette
├── lighting defaults
├── environmental features
├── season variants
├── reference_asset_ids
└── valid_from_event_id
```

---

## 6. Image job contract

```text
ImageJob
├── image_job_id
├── world_id
├── source_event_id
├── source_scene_id
├── asset_class
├── status
├── priority
├── generation_number
├── idempotency_key
├── image_prompt_spec_id
├── workflow_profile_id
├── model_profile_id
├── visual_profile_versions[]
├── outfit_version_ids[]
├── location_visual_profile_id?
├── reference_asset_ids[]
├── seed
├── width
├── height
├── expected_outputs
├── external_prompt_id?
├── attempt
├── max_attempts
├── error_class?
├── created_at
├── started_at?
└── completed_at?
```

Statuses:

```text
PENDING
READY
SUBMITTED
RUNNING
SUCCEEDED
QUALITY_REJECTED
FAILED
CANCELLED
DEAD_LETTER
```

---

## 7. Image prompt specification

The prompt-writing model or deterministic template returns structure, not only one string.

```text
ImagePromptSpecification
├── source_event_facts
├── subject_specs[]
├── interaction
├── location
├── time_weather_lighting
├── composition
├── camera
├── expressions
├── pose_constraints
├── visible_injuries
├── props
├── style_profile
├── positive_prompt
├── negative_prompt
├── reference_bindings
├── content_classification
├── prohibited_additions
└── provenance
```

The application validates every subject/entity/reference ID against the committed scene.

### 7.1 Prohibited additions

At minimum:

- no additional named characters;
- no new injuries;
- no item absent from event/location state;
- no changed hair/eyes/species;
- no romantic intimacy beyond event facts;
- no graphic detail beyond rating;
- no text/logos unless intentionally requested;
- no franchise or living-artist imitation.

---

## 8. ComfyUI adapter

ComfyUI’s local server accepts workflows exported in API format. Its `/prompt` endpoint validates and queues a workflow and returns a prompt identifier or validation errors. `/ws`, `/history/{prompt_id}`, `/view`, `/system_stats`, and queue endpoints support monitoring and retrieval.

### 8.1 Internal protocol

```python
class ImageExecutionGateway(Protocol):
    async def submit(self, request: ImageExecutionRequest) -> ImageSubmission: ...
    async def get_status(self, external_id: str) -> ImageExecutionStatus: ...
    async def cancel(self, external_id: str) -> None: ...
    async def fetch_outputs(self, external_id: str) -> tuple[GeneratedAsset, ...]: ...
    async def health(self) -> ImageWorkerHealth: ...
```

### 8.2 Workflow export

Store exported API-format workflow JSON in the repository or object storage, referenced by immutable hash. Do not scrape the interactive UI graph at runtime.

### 8.3 Workflow profile

```text
ImageWorkflowProfile
├── workflow_profile_id
├── name
├── version
├── workflow_object_key
├── workflow_hash
├── required_node_types
├── required_model_assets
├── input_bindings
├── output_node_ids
├── supported_asset_classes
├── default_dimensions
├── safety_policy_version
└── active
```

### 8.4 Binding layer

Node IDs are isolated in a workflow binding adapter:

```yaml
positive_prompt: "6.inputs.text"
negative_prompt: "7.inputs.text"
seed: "3.inputs.seed"
width: "5.inputs.width"
height: "5.inputs.height"
reference_image_1: "21.inputs.image"
```

Application services refer to semantic fields, not node IDs.

### 8.5 Submission lifecycle

1. claim `READY` image job;
2. load and verify workflow hash;
3. validate required models/nodes against worker capabilities;
4. bind prompt/reference/seed/dimensions;
5. submit `POST /prompt`;
6. store returned prompt ID;
7. monitor WebSocket or poll history;
8. retrieve outputs;
9. verify file hashes and metadata;
10. store assets in object storage;
11. run quality checks;
12. mark succeeded or retry/dead-letter;
13. publish gallery/timeline outbox event.

### 8.6 Monitoring

WebSocket is preferred for progress, with history polling as recovery. The application must tolerate:

- missed WebSocket events;
- reconnect;
- ComfyUI restart;
- history already complete before monitor attaches;
- an external prompt ID unknown after history cleanup.

---

## 9. Worker capability probe

At worker registration, query:

- `/system_stats`;
- `/features` where available;
- `/object_info` or required nodes;
- installed model asset manifest maintained locally;
- workflow dry validation.

Generate a capability record containing:

- GPU/device and memory;
- available workflows;
- required node versions;
- installed checkpoint/LoRA/control assets and hashes;
- maximum tested dimensions;
- current queue depth;
- health timestamp.

Do not submit a job to a worker missing a pinned model or custom node.

---

## 10. Model and asset management

### 10.1 Pinning

Record cryptographic hashes for:

- base checkpoint;
- VAE;
- text encoders;
- character LoRAs;
- control adapters;
- custom nodes and versions;
- workflow JSON;
- reference images.

Never share proprietary or unauthorized model files in project exports.

### 10.2 Licensing registry

Every visual model/LoRA/node includes:

- source;
- license;
- commercial/private-use status;
- attribution requirements;
- restrictions;
- hash;
- date reviewed.

No asset enters active profiles without review.

### 10.3 Custom-node security

ComfyUI custom nodes execute code. Treat them like Python dependencies:

- use minimal set;
- pin commit/version;
- inspect source and permissions;
- do not auto-update;
- run worker with restricted network/filesystem access where practical;
- maintain a tested lock/manifest.

---

## 11. Visual continuity strategy

Use a layered strategy rather than relying on text prompts alone.

### 11.1 Stage 4 baseline

- canonical reference sheet for each focus character;
- canonical portrait and expressions;
- versioned textual visual profile;
- stable style profile;
- fixed aspect ratio families;
- stored seeds;
- reference-image conditioning supported by selected workflow;
- one or more location reference backgrounds.

### 11.2 Optional later enhancements

- character-specific visual LoRAs;
- multi-reference conditioning;
- pose/control maps;
- regional style adapters;
- automated face/identity embeddings;
- outfit-specific reference banks.

These require benchmark and license review.

### 11.3 Multi-character scenes

The prompt specification declares:

- exact subject count;
- subject-to-reference binding;
- left/right/front/back placement;
- relative height;
- outfit;
- interaction and contact;
- expression;
- camera framing.

If the selected workflow cannot reliably support the number of distinct subjects, use:

- a two-character crop;
- separate portraits over background;
- a composition assembled in the frontend;
- one event CG focused on the primary subjects.

Do not keep retrying an unsupported composition indefinitely.

---

## 12. Visual-novel presentation

A visual-novel scene may combine:

- reusable location background;
- one to three character portraits/sprites;
- expression variants;
- dialogue box;
- optional committed-event CG;
- ambient effects.

This presentation is cheaper, faster, and more consistent than generating a full image per action.

The timeline stores references to assets and presentation instructions, not flattened screenshots only.

---

## 13. Quality checks

### 13.1 Deterministic checks

- expected output count;
- valid file format;
- minimum resolution;
- image decodes successfully;
- no duplicate file hash;
- prompt/workflow metadata present;
- content classification matches job;
- subject count plausibility if a detector is configured.

### 13.2 Model-assisted checks

Optional vision evaluator may assess:

- character identity;
- hair/eyes/species features;
- outfit;
- number of characters;
- location match;
- visible injuries;
- pose/action match;
- obvious anatomy/rendering defects;
- prohibited content.

The evaluator returns scores and issue codes; it never modifies canon.

### 13.3 Retry policy

Default:

```text
attempt 1: canonical prompt + seed
attempt 2: same facts, revised negative/composition constraints, new seed
attempt 3: simplified composition or fallback asset class
then: dead-letter/manual review
```

Do not use an identity error as a reason to rewrite the canonical visual profile automatically.

### 13.4 Display selection

A generated asset may be:

```text
AUTO_SELECTED
USER_SELECTED
REJECTED
HIDDEN
SUPERSEDED
```

The timeline displays one selected generation but gallery audit can show alternatives according to settings.

---

## 14. Object storage

Store binaries in local S3-compatible object storage or equivalent. PostgreSQL stores:

- object key;
- bucket;
- content type;
- byte size;
- checksum;
- dimensions;
- metadata;
- source job;
- visibility/status.

Object-key example:

```text
worlds/{world_id}/images/{event_id}/{job_id}/{asset_id}.webp
```

Use immutable object keys. New edits create new assets.

### 14.1 Derivatives

Generate:

- original;
- web-optimized large asset;
- thumbnail;
- optional portrait crop.

All derivatives reference the original asset ID.

---

## 15. Content and privacy boundaries

- no real-person face/voice references in free external inference flows;
- no sexualized minors;
- no explicit sexual content under default young-adult configuration;
- soft-dark violence remains non-graphic;
- sensitive image jobs may require user approval;
- metadata strips local filesystem paths and secrets;
- ComfyUI should not be exposed unauthenticated to the public internet;
- upload endpoints accept only validated files with size/type limits.

---

## 16. Failure and recovery

### 16.1 ComfyUI unavailable

- image jobs remain pending/retryable;
- simulation continues;
- UI displays placeholder;
- operations dashboard shows backlog;
- no canonical rollback.

### 16.2 Submission uncertain

Query history using stored client/prompt metadata. If external identity is unknown, a new generation may be submitted only after checking idempotency and accepting possible orphan cleanup.

### 16.3 Asset stored but job not acknowledged

Checksum/object metadata makes storage idempotent. Reconciliation attaches the existing asset and completes the job.

### 16.4 Workflow version removed

Keep referenced workflow artefacts and model manifests for old jobs. If exact regeneration is unavailable, mark reproducibility status rather than silently using a different workflow.

---

## 17. API and UI integration

REST endpoints and WebSocket events are defined in `17`.

UI states:

- no image requested;
- queued;
- generating;
- available;
- quality rejected/retrying;
- failed;
- user regeneration options.

An image finishing days later is inserted at the source event’s timeline position and also emits a “new asset available” notification.

---

## 18. Required tests

### Adapter tests

- workflow binding;
- `/prompt` validation failure;
- successful prompt ID;
- WebSocket completion;
- missed WebSocket + history recovery;
- output download and checksum;
- cancellation;
- ComfyUI restart;
- duplicate submission idempotency.

### Continuity tests

- appearance version selected for event date;
- outfit version matches committed state;
- healed scar appears only after canonical event;
- two characters use correct references;
- child/generation appearance does not reuse parent identity accidentally.

### Policy tests

- unresolved action cannot create job;
- graphic/sexual prohibited job is blocked;
- image does not create an event effect;
- failed image does not block phase completion;
- custom workflow missing required node is rejected before queueing.

### Soak test

Run a simulated week with the image worker offline, then restore it and verify backlog processing without duplicate assets or phase impact.

---

## 19. Definition of done

The image subsystem is complete when:

- images originate only from committed events;
- jobs are durable, idempotent, and asynchronous;
- visual state is versioned and event-sourced;
- ComfyUI workflow/model/node versions are pinned;
- a worker restart and missed WebSocket do not lose jobs;
- visual failures cannot alter or block canon;
- multi-character limitations have deterministic fallbacks;
- content/licensing/security policies are enforced;
- gallery assets retain complete provenance and reproducibility status.

---

## 20. Official references

- ComfyUI server routes: <https://docs.comfy.org/development/comfyui-server/comms_routes>
- ComfyUI API examples: <https://docs.comfy.org/development/comfyui-server/api-examples>
- ComfyUI server overview: <https://docs.comfy.org/development/comfyui-server/comms_overview>
- ComfyUI server messages: <https://docs.comfy.org/development/comfyui-server/comms_messages>
