# `S4-IMG-002` — Visual profiles, prompt compiler, continuity

**Stage:** 4  
**Workstream:** IMG  
**Status:** READY  
**Priority:** P0  
**Depends on:** S4-IMG-001 / STORAGE

## Objective

Versioned world/character/location visual profiles and compile image prompts from
committed structured scene state. Characters do not author their own authoritative
visual prompts.

## Acceptance

- [x] Visual profile records (`visual_profile` table, `VisualProfileRow`/`VisualProfileRecord`, `SqlAlchemyVisualProfileRepository`)
- [x] Prompt compiler from committed state (`application/images/prompt_compiler.py`, `compile_prompt()`)
- [x] Continuity version fields (`profile_version`, `valid_from_event_id`, `supersedes_profile_id` on `visual_profile`)
- [x] Unit tests (`test_prompt_compiler.py` — 8 tests)
