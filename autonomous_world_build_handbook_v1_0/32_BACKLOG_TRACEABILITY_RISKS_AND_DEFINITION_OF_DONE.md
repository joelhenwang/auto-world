# Backlog, Requirements Traceability, Risk Register, and Definition of Done

**Version:** 1.0  
**Status:** Normative planning and stage-audit index  
**Primary owners:** parent agent, QA owner, architecture reviewer, project owner

---

## 1. Purpose

This document connects the product requirements to implementation stages, subsystem documents, task packets, and verification evidence. It also maintains the initial risk register and defines what “done” means at task, feature, stage, and product levels.

The task lists in `25`–`30` are the executable stage plans. This file is the cross-stage control index.

---

## 2. Status vocabulary

Use these values in project status files:

```text
NOT_STARTED
CONTRACT_DRAFT
READY
IN_PROGRESS
BLOCKED
IN_REVIEW
MERGED
VERIFIED
DEFERRED
CANCELLED
```

A task is not `VERIFIED` merely because code was merged. Required acceptance tests and evidence must pass.

---

## 3. Stage backlog summary

| Stage | Task IDs | Outcome |
|---|---|---|
| 0 | `S0-ENG-001` … `S0-QA-001` | Repository, contracts, persistence, deterministic event/task foundation |
| 1 | `S1-DB-001` … `S1-QA-001` | First autonomous three-phase day with two characters |
| 2 | `S2-DB-001` … `S2-QA-001` | Coherent seven-day world with four characters, Director, NPC, beliefs, travel, diaries |
| 3 | `S3-DB-001` … `S3-QA-001` | Autonomous month, RAG, arcs/factions, rules, injuries, quality controls |
| 4 | `S4-BENCH-001` … `S4-QA-001` | Distributed local inference and asynchronous visual pipeline |
| 5 | `S5-DB-001` … `S5-QA-001` | Adaptive long-horizon simulation and three generations |

The exact Stage 0 IDs are in `25_STAGE_0_FOUNDATION.md`; later IDs are in their respective stage documents.

---

## 4. Requirements traceability matrix

### 4.1 Product principles

| Requirement | Primary design documents | Implemented/proven by |
|---|---|---|
| PRN-001 Coherence over spectacle | `03`, `04`, `05`, `21` | All stages; invariant/quality gates |
| PRN-002 Agency over forced plot | `07`, `08`, `09`, `15` | Stages 1–3; refusal/plan/Director tests |
| PRN-003 Simulation truth, narrative presentation | `03`, `05`, `07`, `10`, `15` | Stage 1 scene commit; Stage 3 rules |
| PRN-004 Perspective is real | `05`, `08`, `11`, `17`, `18` | Stages 1–3 leakage suites |
| PRN-005 Quiet life is part of the world | `07`, `09`, `15`, `21` | Stages 1–3 action/activation/repetition review |
| PRN-006 Explicit user power | `02`, `05`, `17`, `18`, `22` | Stage 1 player; Stage 2 Director; Stage 3 deity |
| PRN-007 Local-first evolution | `04`, `12`, `14`, `20`, `29` | Stages 0–4 provider abstraction/local migration |
| PRN-008 Inspectability | `06`, `17`, `18`, `21`, `22` | All stages, provenance/trace/UI/evidence |

### 4.2 User roles and modes

| Requirement | Documents | Stage/gate |
|---|---|---|
| ROLE-001 Watcher | `02`, `17`, `18`, `22` | Stage 1 read UI; Stage 2 omniscient views |
| ROLE-002 Director | `02`, `09`, `17`, `18` | Stage 2 command/proposal and permissions |
| ROLE-003 Deity | `02`, `03`, `06`, `17`, `18`, `22` | Stage 3 explicit high-impact commands/audit |
| ROLE-004 Player | `02`, `07`, `11`, `17`, `18` | Stage 1 input boundary/perspective tests |
| MODE-001 Automatic | `07`, `14`, `17`, `18` | Stage 1 auto day; later soaks |
| MODE-002 Manual phase stepping | `07`, `17`, `18` | Stage 1 |
| MODE-003 Debug stepping | `13`, `14`, `17`, `18`, `22` | Stage 1–2 diagnostics |
| MODE-004 Macro simulation | `07`, `09`, `30` | Stage 5 |

### 4.3 World and time

| Requirement | Primary docs | Stage/task evidence |
|---|---|---|
| FR-WORLD-001 one canonical world/timeline | `02`, `03`, `04`, `06` | S0-DB/S0 seed; DB constraints |
| FR-WORLD-002 ten phases | `05`, `07` | S1 contracts; S2-SIM-001 full calendar |
| FR-WORLD-003 deterministic tick first | `07`, `14` | S0 deterministic engine; phase scenario |
| FR-WORLD-004 pause while stopped | `07`, `14`, `22` | S0/S1 restart; S5 explicit macro command |
| FR-WORLD-005 persistent activities | `05`, `06`, `07` | S2-SIM-001 |
| FR-WORLD-006 interruption conditions | `05`, `07` | S2 activity tests |
| FR-WORLD-007 route travel | `07`, `09`, `23` | S2-SIM-001/map tests |
| FR-WORLD-008 quiet phases | `07`, `08`, `15` | S1/S2 activation tests |
| FR-WORLD-009 phase completion contract | `05`, `07`, `14`, `16` | S1-ORCH; phase barrier fault tests |
| FR-WORLD-010 images nonblocking | `14`, `16`, `29` | S4 image outage gate |

### 4.4 Characters

| Requirement | Primary docs | Stage/task evidence |
|---|---|---|
| FR-CHAR-001 2 main/2 sub-main | `02`, `08`, `23` | Stage 2 seed/run |
| FR-CHAR-002 versioned card | `05`, `06`, `08`, `23` | S0 schema/seed; card tests |
| FR-CHAR-003 dynamic state | `06`, `08`, `10`, `11` | Stages 0–3 projections |
| FR-CHAR-004 no memory transcript in card | `08`, `11`, `15` | Context/card tests |
| FR-CHAR-005 sourced evolution | `06`, `08`, `11` | S3 monthly reflection/version tests |
| FR-CHAR-006 explicit foundational retcon | `03`, `05`, `06`, `17` | S3 deity/taint audit; S5 retcon test |
| FR-CHAR-007 false beliefs/lies/forgetting | `08`, `11` | S2 claims/beliefs; S3 memory tests |
| FR-CHAR-008 directional relationships | `06`, `08`, `11` | S2-CHAR-001 |
| FR-CHAR-009 multi-phase plans | `07`, `08` | S2-CHAR/SIM tests |
| FR-CHAR-010 monthly identity reflection | `08`, `11`, `13`, `28` | S3-MEM-003 |
| FR-CHAR-011 ageing/family/disability/death | `08`, `10`, `30` | S3 injuries/death; S5 lineage |
| FR-CHAR-012 constrained return | `08`, `09`, `10` | S3 high-impact tests |

### 4.5 Actions, scenes, and outcomes

| Requirement | Primary docs | Stage/task evidence |
|---|---|---|
| FR-SCENE-001 same sealed snapshot | `05`, `06`, `07`, `13` | S1 snapshot assertions |
| FR-SCENE-002 free intent/stable family/effects | `05`, `07`, `15` | S1/S2 schema corpus |
| FR-SCENE-003 one primary proposal | `05`, `06`, `07` | DB unique + orchestration tests |
| FR-SCENE-004 safe quiet actions | `07`, `08`, `15` | S1 action fixtures |
| FR-SCENE-005 scene assembly | `07`, `13` | S1/S2 scene tests |
| FR-SCENE-006 no authored other reaction | `05`, `07`, `13`, `15` | S1 adversarial prompt tests |
| FR-SCENE-007 bounded reactions | `07`, `13` | S1/S2 reaction graph |
| FR-SCENE-008 hard beat budgets | `07`, `13`, `15` | S1/S2 loop tests |
| FR-SCENE-009 resolution levels | `05`, `07`, `10` | resolver contract tests |
| FR-SCENE-010 no model direct mutation | `03`, `04`, `05`, `13` | architecture import/effect tests |
| FR-SCENE-011 typed validated effects | `05`, `06`, `07`, `10` | all event/effect gates |
| FR-SCENE-012 commit before narration | `05`, `07`, `13`, `15` | S1 transaction/narration tests |
| FR-SCENE-013 bounded invalid ladder | `12`, `13`, `15` | S1 model failure corpus |
| FR-SCENE-014 causal reaction/no global leakage | `07`, `11`, `13` | S1/S2 scene ordering tests |

### 4.6 World Engine and Director

| Requirement | Primary docs | Stage/task evidence |
|---|---|---|
| FR-DIR-001 engine/director split | `03`, `04`, `09`, `13` | S2-WORLD-001 architecture tests |
| FR-DIR-002 deterministic ownership | `07`, `09`, `10` | S0/S2/S3 domain tests |
| FR-DIR-003 proposal scope | `09`, `13`, `15` | S2 Director schemas |
| FR-DIR-004 omniscient/no leakage | `09`, `11`, `15` | S2 secret disclosure tests |
| FR-DIR-005 triggered, not every phase | `07`, `09`, `27` | S2 trigger/cooldown tests |
| FR-DIR-006 pacing/trope history | `09`, `21`, `28` | S3-WORLD-002 |
| FR-DIR-007 major arc budget | `09`, `28`, `30` | S3 arc state; S5 generation arc |
| FR-DIR-008 spotlight vs outcome bias | `03`, `09`, `10` | config/resolver tests |
| FR-DIR-009 privilege-limited world changes | `05`, `09`, `17`, `22` | S3 high-impact authorization |
| FR-DIR-010 adaptive story, no forced agency | `08`, `09`, `15` | Stage 2/3 human and scenario review |

### 4.7 NPCs and society

| Requirement | Primary docs | Stage/task evidence |
|---|---|---|
| FR-NPC-001 Director-only identity proposal | `09`, `13`, `15` | S2-WORLD-002 |
| FR-NPC-002 registry dedup/validation | `06`, `09` | S2 duplicate fixture |
| FR-NPC-003 lifecycle classes | `08`, `09`, `30` | S2 and S5 schema tests |
| FR-NPC-004 bounded persistence | `09`, `27` | TTL/archive tests |
| FR-NPC-005 no automatic focus promotion | `09`, `30` | S2/S5 slot constraints |
| FR-NPC-006 batch low-importance NPCs | `09`, `13` | S2 NPC graph tests |
| FR-NPC-007 budgets | `09`, `27` | S2 budget tests |
| FR-SOCIETY-001 faction state | `09`, `28` | S3-WORLD-001 |
| FR-SOCIETY-002 aggregate economy/population | `09`, `28`, `30` | S3/S5 background simulation |

### 4.8 Stats, skills, magic, and injury

| Requirement | Primary docs | Stage/task evidence |
|---|---|---|
| FR-RULE-001 common 0–100 | `08`, `10` | S3-RULES-001 |
| FR-RULE-002 potential/growth | `10` | S3 property tests |
| FR-RULE-003 species/age/etc. common scale | `10`, `30` | S3/S5 calculations |
| FR-RULE-004 skills separate/evidence | `10` | S3 progression tests |
| FR-RULE-005 constrained narrative awards | `10`, `15` | S3 evidence gate |
| FR-RULE-006 no HP | `03`, `10` | schema grep/architecture test |
| FR-RULE-007 injuries not HP | `06`, `10` | S3-RULES-003 |
| FR-RULE-008 stamina/mana resources | `08`, `10` | S1 stamina; S3 mana |
| FR-RULE-009 structured magic | `10`, `23` | S3-RULES-002 |
| FR-RULE-010 hybrid combat | `07`, `10`, `13` | S3 resolver scenarios |
| FR-RULE-011 causal weaker victory | `10`, `21` | S3 combat matrix |

### 4.9 Perception, knowledge, and memory

| Requirement | Primary docs | Stage/task evidence |
|---|---|---|
| FR-MEM-001 separate record types | `05`, `06`, `11` | S2 schema/knowledge tests |
| FR-MEM-002 observer-specific observations | `07`, `11` | S1/S2 leakage tests |
| FR-MEM-003 ambiguity/contradiction | `08`, `11` | S2 witness fixtures |
| FR-MEM-004 observation for observed event | `05`, `11` | event commit assertions |
| FR-MEM-005 salience memories | `11` | S2/S3 memory tests |
| FR-MEM-006 recent relational memory | `06`, `11` | Stage 1/2 context |
| FR-MEM-007 daily compaction | `11`, `13` | S2-MEM-001 |
| FR-MEM-008 monthly compaction | `08`, `11`, `13` | S3-MEM-003 |
| FR-MEM-009 forgetting as retrieval decay | `11` | S3 tests |
| FR-MEM-010 provenance/confidence/visibility | `06`, `11` | S2/S3 constraints |
| FR-MEM-011 owner/visibility prefilter | `06`, `11`, `22` | S3 adversarial retrieval |
| FR-MEM-012 composite retrieval score | `11`, `28` | S3-MEM-002 |
| FR-MEM-013 untrusted retrieved text | `11`, `15`, `22` | prompt-injection tests |

### 4.10 Images

| Requirement | Primary docs | Stage/task evidence |
|---|---|---|
| FR-IMG-001 committed source only | `05`, `14`, `16` | S4 image job transaction tests |
| FR-IMG-002 reusable assets/event CGs | `16`, `18` | S4 UI/asset review |
| FR-IMG-003 versioned appearances/locations | `06`, `16` | S4 visual schema |
| FR-IMG-004 structured prompt compilation | `16` | S4 compiler tests |
| FR-IMG-005 async/idempotent/nonblocking | `14`, `16`, `29` | S4 outage/duplicate tests |
| FR-IMG-006 images not canonical | `03`, `16`, `18` | API/domain constraints |
| FR-IMG-007 late historical placement | `16`, `17`, `18` | S4 E2E |

### 4.11 User-facing outputs

| Requirement | Primary docs | Stage/task evidence |
|---|---|---|
| FR-UI-001 timeline | `17`, `18` | Stage 1 onward |
| FR-UI-002 diaries | `11`, `17`, `18` | Stage 2 |
| FR-UI-003 visual-novel scenes | `15`, `16`, `18` | text Stage 1; visual Stage 4 |
| FR-UI-004 encyclopedia | `11`, `17`, `18` | Stage 2/3 |
| FR-UI-005 perspective map | `09`, `17`, `18` | Stage 2 |
| FR-UI-006 character details by role | `08`, `10`, `11`, `18` | Stages 1–3 |
| FR-UI-007 queues/workers | `14`, `17`, `18` | Stage 1 task; Stage 4 hosts |
| FR-UI-008 controls/retry | `14`, `17`, `18` | Stage 1 onward |

### 4.12 End conditions and generations

| Requirement | Primary docs | Stage/task evidence |
|---|---|---|
| FR-END-001 three end conditions | `02`, `09`, `30` | S5-END-001 |
| FR-END-002 sustained peace | `09`, `30` | S5 ending fixtures |
| FR-END-003 eradication continuation check | `09`, `30` | S5 ending fixtures |
| FR-END-004 max three generations | `08`, `09`, `30` | DB constraint/gate |
| FR-END-005 time compression/expansion | `07`, `09`, `30` | S5-MACRO |
| FR-END-006 no private memory inheritance | `11`, `30` | S5 lineage leakage tests |

### 4.13 Non-functional requirements

| Requirement | Primary docs | Verification |
|---|---|---|
| NFR-COR-001 zero hard invariants | `05`, `21` | Every stage soak |
| NFR-COR-002 atomic scene/event | `06`, `07` | DB integration/fault tests |
| NFR-COR-003 duplicate delivery safe | `06`, `14` | idempotency/fencing tests |
| NFR-COR-004 projection provenance | `06`, `22` | audits |
| NFR-REL-001 restart-safe | `14`, `21`, `22` | per-stage process-kill matrix |
| NFR-REL-002 external failures bounded | `12`, `14`, `16` | provider/image/worker tests |
| NFR-REL-003 no partially canonical next phase | `07`, `14` | barrier tests |
| NFR-REL-004 image downtime isolated | `16`, `29` | Stage 4 |
| NFR-SEC-001 synthetic OpenRouter data | `12`, `22` | prompt/privacy review |
| NFR-SEC-002 secret handling | `19`, `20`, `22` | secret scans/log tests |
| NFR-SEC-003 least-privilege tools | `11`, `13`, `22` | capability tests |
| NFR-SEC-004 injection isolation | `11`, `15`, `22` | adversarial corpus |
| NFR-SEC-005 server-side roles | `17`, `18`, `22` | API auth tests |
| NFR-PERF-001 measured latency | `21`, `22`, `29` | benchmark reports |
| NFR-PERF-002 exact vectors first | `06`, `11`, `28` | query benchmark/ADR |
| NFR-PERF-003 remote calls outside TX | `06`, `12`, `14` | architecture/concurrency review |
| NFR-PERF-004 portable identity | `04`, `12`, `29` | Stage 4 failover |
| NFR-MNT-001 domain infra independence | `04`, `19`, `21` | import/lint architecture test |
| NFR-MNT-002 stable provider gateway | `12` | adapter contract suite |
| NFR-MNT-003 reviewed migrations | `06`, `20`, `31` | CI/review evidence |
| NFR-MNT-004 versioned contracts | `05`, `06`, `12`, `15`, `17` | schema registry/change control |
| NFR-MNT-005 strict static/tests | `19`, `20`, `21` | CI |
| NFR-OBS-001 model call correlation | `12`, `14`, `22` | trace integration tests |
| NFR-OBS-002 transition audit | `06`, `14`, `22` | audit logs |
| NFR-OBS-003 provider usage | `12`, `22` | metrics/budget ledger |
| NFR-OBS-004 sensitive log redaction | `12`, `22` | log snapshot tests |

### 4.14 Narrative-quality requirements

| Requirement | Primary docs | Verification |
|---|---|---|
| NAR-001 emotion through behaviour/subtext | `08`, `15`, `21` | prompt corpus, evaluator rubric, human review |
| NAR-002 rare dramatic one-liners | `15`, `21`, `28` | phrase/style-rate metric and month review |
| NAR-003 friendship not automatic romance | `08`, `09`, `21` | relationship/romance scenario tests |
| NAR-004 reciprocal romance that may fail | `08`, `09`, `21` | reciprocal-evidence and refusal tests |
| NAR-005 motivated villains/rivals | `09`, `15`, `23` | antagonist-card review and scenario rubric |
| NAR-006 side characters not praise devices | `09`, `15`, `21` | NPC-goal/agency rubric |
| NAR-007 quiet scenes remain valid | `07`, `09`, `15`, `21` | quiet-day fixtures and human review |
| NAR-008 failure creates consequences, not automatic power-up | `07`, `10`, `15`, `21` | failure-resolution fixtures |
| NAR-009 repetition tracking and cooldowns | `09`, `21`, `28` | trope/location/phrase novelty metrics |
| NAR-010 distributed exposition | `09`, `15`, `21`, `23` | exposition-density rubric and scene review |

---

## 5. Initial risk register

| ID | Risk | Likelihood | Impact | Mitigation/owner | Trigger/evidence |
|---|---|---:|---:|---|---|
| R-001 | Agents become chatbots sharing global context instead of isolated actors | M | Critical | ContextAssembler/access-policy tests; KNOW owner | Any cross-character private fact in prompt |
| R-002 | Model prose mutates canon | M | Critical | Typed effects + transaction service; SIM/DB | State change without event/effect |
| R-003 | Duplicate task applies injury/movement twice | M | Critical | Idempotency/fencing/unique keys; ORCH/DB | Duplicate source/effect or projection drift |
| R-004 | Character authors another’s hidden reaction | H | High | Separate reaction graph/prompts/tests; GRAPH | Other actor intent in proposal |
| R-005 | Director leaks omniscient secrets | M | Critical | Disclosure paths/perception engine; WORLD/KNOW | Unauthorized observation/diary |
| R-006 | Free OpenRouter model unavailable, throttled, changed, or removed | H | High | Runtime capability/quota probes, fake model, local migration; MODEL | 429/model lookup/capability mismatch |
| R-007 | Free endpoint data/privacy policy unsuitable | M | High | Synthetic-only policy; local-only flag; SEC | Nonfiction/private data in request |
| R-008 | Structured output unsupported by selected endpoint | H | Medium | Capability mode, healing, local validation/regeneration; MODEL | Schema ignored/invalid output rise |
| R-009 | Embedding dimension/model changes | M | High | Version registry/probe/new column migration; MEM/DB | Probe dimension mismatch |
| R-010 | Vector retrieval leaks across owners | M | Critical | Mandatory SQL predicates and adversarial tests; MEM/SEC | Unauthorized candidate before prompt |
| R-011 | Memory summaries hallucinate facts | H | High | Source IDs, constrained summarizer, extractive fallback; MEM | Unsupported summary statement |
| R-012 | Memory grows without bound | H | High | tiers/compaction/token budgets/metrics; MEM | Context/token growth trend |
| R-013 | Overcompaction erases commitments/identity | M | High | structured commitments/permanent classes/source retention; MEM | Promise recall benchmark decline |
| R-014 | Character personalities collapse into same voice | M | Medium | cards, corpus, evaluator, distinct fixtures; MODEL/CHAR | voice classifier/human score |
| R-015 | Story becomes repetitive or melodramatic | H | High | trope/novelty/cooldowns/quiet policy; WORLD/QA | repetition metrics/human review |
| R-016 | Director forces intended plot/romance | M | High | agency rules, reciprocal evidence, refusal tests; WORLD/CHAR | action contradicts goals without cause |
| R-017 | NPC explosion | H | Medium | registry, budgets, TTL/archive; WORLD | active/new NPC thresholds |
| R-018 | Pure event sourcing becomes operationally expensive | M | Medium | event + projection hybrid; DB | slow rebuild/query complexity |
| R-019 | JSONB becomes uncontrolled schema substitute | M | High | relational schema policy/review; DB | queried domain fields buried in JSONB |
| R-020 | Database transaction contains remote model call | M | Critical | architecture tests/UoW boundary; DB/ORCH | long lock/external I/O in TX |
| R-021 | Phase starts without enough provider budget to finish | H early | High | reservation/fallback; MODEL/ORCH | partial phase due quota |
| R-022 | Beat/model-call loop consumes unbounded requests | M | High | hard budgets/counters; GRAPH/ORCH | call count exceeds contract |
| R-023 | Retcon leaves invisible contradictions | M | High | taint/audit/explicit warnings; DB/QA | dependent projections inconsistent |
| R-024 | Rules are too vague and resolver grants impossible outcomes | H | High | deterministic feasible envelope; RULES | unsupported combat/magic result |
| R-025 | Rules are too rigid and story becomes mechanical | M | Medium | model choice within envelope; WORLD/MODEL | low human engagement score |
| R-026 | HP sneaks back into implementation | L | Medium | architecture/schema/grep tests; RULES | `hp` domain field |
| R-027 | Local ROCm serving stack is unstable | H | High | benchmark/pin/fallback/soak; S4-BENCH | startup/OOM/kernel failures |
| R-028 | Character identity tied to machine/session/KV cache | M | Critical | stateless context/gateway failover tests; MODEL | behavior/state lost on endpoint move |
| R-029 | Distributed stale worker commits after failover | M | Critical | fencing tokens/generation checks; ORCH | late duplicate/overwrite |
| R-030 | ComfyUI/image backlog blocks simulation | M | High | separate outbox/queue/nonblocking barrier; IMG | phase waits on image |
| R-031 | Visual identity inconsistency | H | Medium | versioned profiles/references/QC; IMG | review mismatch rates |
| R-032 | Image introduces noncanonical detail | H | Medium | illustrations only/no state extraction; IMG | state change sourced from image |
| R-033 | Temporal/plugin adoption adds premature complexity | M | Medium | ADR/interface/evidence-based adoption; ORCH | workflow migration slows stage |
| R-034 | Parallel agents implement competing contracts | H | High | contract freeze/file ownership; parent | merge conflicts/schema divergence |
| R-035 | Multi-session context is lost | H | High | status/task/handoff/templates; parent | new agent cannot reproduce next step |
| R-036 | Migration chain diverges across subagents | M | High | reservation/one owner/integration order; DB | multiple heads/conflicts |
| R-037 | Generated API/client drifts from server contract | M | Medium | OpenAPI generation/CI no-diff; API/UI | local duplicate DTO mismatch |
| R-038 | Logs expose prompts, secrets, provider keys | M | Critical | structured redaction/no raw defaults/scans; OPS | secret scanner/log snapshot |
| R-039 | Deity privileges bypass audit/auth | M | Critical | server-side RBAC, explicit event, confirmation; API/SEC | direct table update/unlogged command |
| R-040 | Three-generation run is computationally infeasible | H | High | macro resolution/time compression; MACRO | projected phase/call count |
| R-041 | Macro summaries overwrite detailed facts | M | Critical | source ranges/effects/no silent rewrite; MACRO | summary-state contradiction |
| R-042 | Successor inherits private memories | M | Critical | knowledge-channel derivation/leakage test; LINEAGE | inaccessible parent memory in context |
| R-043 | Genealogy/age state becomes impossible | M | High | constraints/audits; LINEAGE/DB | cycle/age violation |
| R-044 | Peace/eradication ends world prematurely | M | High | sustained structured thresholds/audit; END | single-event ending |
| R-045 | Model/checkpoint licenses conflict with future commercialization | M | High | license registry/review before adoption; ARCH/OPS | missing/incompatible license |
| R-046 | Backups exist but restore fails | M | Critical | scheduled restore drills; OPS | unverified backup age |
| R-047 | Exact vector search later becomes slow | L early/M later | Medium | measure, partition, HNSW ADR; MEM/DB | p95/query plan threshold |
| R-048 | UI accidentally exposes watcher data in player mode | M | Critical | server-side perspective DTOs/E2E; API/UI | hidden field in payload |
| R-049 | Fake-model tests pass but live quality is unusable | M | High | sampled live corpus/human review; MODEL/QA | quality delta |
| R-050 | Live-model variability makes tests flaky | H | Medium | no live calls in deterministic gate; QA | nondeterministic CI failure |

Risk status should be maintained in `docs/status/` during implementation. New critical/high risks require an owner and mitigation before stage promotion.

---

## 6. Definition of Ready

A task is ready when:

- objective and exclusions are explicit;
- upstream contracts are frozen and referenced by commit/version;
- writable paths and migration ownership are assigned;
- dependencies are merged or mocked through agreed interfaces;
- acceptance criteria and test commands exist;
- required fixtures/data are available;
- security/knowledge/content implications are identified;
- no unresolved breaking contract question blocks implementation.

A stage is ready when the previous stage gate passes and the stage contract-freeze pass is complete.

---

## 7. Definition of Done — task

A task is done only when:

- scoped behavior is implemented;
- explicit exclusions were respected;
- unit/integration/migration/fault tests required by packet pass;
- formatting/lint/static/type checks pass for affected scope;
- no secret/sensitive fixture is committed;
- public interfaces and generated artefacts are synchronized;
- migrations were tested from clean and previous-stage fixtures when applicable;
- logs/metrics/provenance are present where required;
- documentation/ADR/traceability changes are included;
- self-review found no unscoped changes;
- reviewer findings are resolved or tracked;
- coherent commits and handoff exist;
- parent integration verification passes.

---

## 8. Definition of Done — vertical feature

A vertical feature normally includes:

```text
contract
validation
persistence/migration
repository/application service
orchestration/task behavior
model/graph adapter if applicable
canonical/derived result
API projection/command
minimal UI/diagnostic visibility if stage requires it
tests including failure and permissions
observability/provenance
documentation
```

A model prompt producing plausible text is not a finished feature.

---

## 9. Definition of Done — stage

A stage is done only when:

- every hard exit gate in the stage document passes;
- all critical/high findings are resolved;
- all tasks required by scope are `VERIFIED`;
- previous-stage gates remain green;
- deterministic scenario and evidence bundle are reproducible;
- fault, leakage, idempotency, migration, and security matrices pass;
- required human narrative/visual review is recorded;
- database/event/projection audit passes;
- docs/ADRs/traceability/reference registry are current;
- deployment/run instructions work from a clean environment;
- a recovery/backup checkpoint exists;
- `main` passes CI;
- the stage is tagged/recorded with versions and known nonblocking risks.

---

## 10. Definition of Done — product

The product is complete for the agreed scope when Stage 5 passes and:

- the world can run in watcher/director/deity/player modes;
- automatic/manual/debug/macro operation works;
- one world progresses through up to three generations;
- end conditions are evaluated correctly;
- canonical history remains auditable and perspective-safe;
- text inference can run locally across the intended hardware;
- image work is asynchronous and visually manageable;
- the timeline, diaries, visual-novel scenes, encyclopedia, map, and genealogy are usable;
- backups/restores and complete export are verified;
- no known critical/high risk remains accepted without an explicit project-owner decision.

---

## 11. Evidence bundle layout

For every stage, produce:

```text
docs/status/evidence/stage-<n>/
├── README.md
├── environment.json
├── versions.json
├── migration_report.md
├── test_report.xml-or-json
├── invariant_report.json
├── leakage_report.json
├── fault_matrix.md
├── performance_report.json
├── provider_capability_report.json
├── quality_review.md
├── screenshots-or-export-links.md
├── known_risks.md
└── checksums.sha256
```

Stage-specific additions:

- Stage 2: seven-day event/diary audit;
- Stage 3: memory/repetition/combat/month export;
- Stage 4: hardware benchmark/distributed traces/visual review;
- Stage 5: macro/genealogy/ending/export audit.

---

## 12. Change impact checklist

Any change to these requires traceability review:

- user role or permission;
- phase/scene state;
- event/effect schema;
- observer/access policy;
- character-card or memory ownership;
- rule formula or high-impact condition;
- model/embedding/image model;
- provider privacy/quota behavior;
- migration strategy;
- orchestration/idempotency semantics;
- API perspective DTO;
- time compression/generation/end condition;
- content rating/safety boundary.

Use `33_REFERENCE_REGISTRY_AND_CHANGE_CONTROL.md` for the formal process.
