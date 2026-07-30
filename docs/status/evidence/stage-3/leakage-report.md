# Stage 2 knowledge and perspective leakage report

**Result:** PASS
**Command:** `uv run pytest backend/tests/unit/application/knowledge/test_leakage.py backend/tests/unit/application/knowledge/test_leakage_corpus.py backend/tests/unit/application/context/test_assembler_leakage.py -s`
**Raw evidence:** `leakage.txt` — 11 passed
**Corpus assertion count:** 496

Verified:

- seeded private beliefs stay owner-scoped across four characters;
- synthetic sealed phrases (>=100 assertion matrix) never cross observers;
- director-only facts never enter character or NPC packages;
- unauthorized secret phrases are scrubbed from consolidation text;
- Stage 1 assembler leakage suite remains green.

No hard leakage finding was observed.
