# Local serving benchmark — `transformers`

- report_id: `bench-transformers-c7b208f80c`
- environment: `local-transformers`
- corpus: `stage4-bench-stage3-rep-v1`
- started: 2026-07-30T01:20:30Z
- finished: 2026-07-30T01:20:30Z

## Summary

- total: 18
- successes: 18
- failures: 0
- structured_valid: 14/17
- fanout_successes: 4/4

## Latency by role (successful)

| Role | n | p50 ms | p95 ms | mean ms |
|---|---:|---:|---:|---:|
| character_decision | 6 | 12.0 | 12.0 | 10.0 |
| character_reaction | 1 | 12.0 | 12.0 | 12.0 |
| daily_summarizer | 1 | 12.0 | 12.0 | 12.0 |
| director_proposal | 1 | 12.0 | 12.0 | 12.0 |
| embedding | 2 | 12.0 | 12.0 | 12.0 |
| monthly_reflector | 2 | 12.0 | 12.0 | 12.0 |
| quality_evaluator | 1 | 12.0 | 12.0 | 12.0 |
| resolver | 2 | 6.0 | 12.0 | 6.0 |
| scene_narrator | 2 | 12.0 | 12.0 | 12.0 |

## Host / software

```json
{
  "host_record": {
    "environment_profile": "local-transformers",
    "hostname": "cursor",
    "machine": "x86_64",
    "processor": "x86_64",
    "python": "3.12.3",
    "release": "6.12.94+",
    "system": "Linux"
  },
  "software": {
    "platform": "Linux-6.12.94+-x86_64-with-glibc2.39",
    "python": "3.12.3",
    "stack_id": "transformers"
  }
}
```
