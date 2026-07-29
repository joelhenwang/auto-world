# Stage 1 deterministic performance and growth summary

**Result:** PASS for bounded Stage 1 fixture; no production p95 claim.

| Measure | Observed evidence |
|---|---|
| Complete fake-model scenario test | 1 passed in 3.5–3.7 seconds |
| Fake model requests | exactly 10 for the three-phase day |
| Frontend production build | 31 modules; 83.82 kB JS / 32.33 kB gzip |
| Frontend component/client tests | 5 passed in 1.7–1.8 seconds |
| Canonical scenes | 3 |
| Primary proposals | 6 |
| Observations / recent memories | 8 / 6 |
| Succeeded task rows | 30 |

Model calls carry no open database transaction. The fixture remains bounded;
long-horizon p95, query-count, and soak measurements begin in later stages.
