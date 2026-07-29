# Stage 1 knowledge and perspective leakage report

**Result:** PASS
**Command:** `uv run pytest backend/tests/unit/application/context/test_assembler_leakage.py backend/tests/integration/test_stage1_api.py`
**Raw evidence:** `leakage.txt` — 7 passed

Verified:

- another character's private beliefs and true directional relationship row do
  not enter a character context;
- untrusted memory delimiters remain data rather than prompt instructions;
- each scene participant carries a distinct non-null knowledge-scope hash;
- character and scene API DTOs omit secret manifests, private beliefs, prompt
  provenance, and context hashes;
- observer-scoped timeline/WebSocket reads admit only world and matching
  character scopes;
- player actions reference known characters and are persisted as attempts, not
  canonical effects.

No hard leakage finding was observed.
