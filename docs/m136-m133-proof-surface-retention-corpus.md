# M136 M133 Proof-Surface Retention Corpus

M134 and M135 show that guarded PPO can retain behavior while shrinking M133's
strict selected-seed proof surface. M136 turns the M133 strict rows themselves
into an explicit corpus and audits how much of that surface later candidates
retain.

## Corpus Build

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.outcome_snippet_corpus \
  --input-run runs/m133_zero_relvel_s60_strict_60ep_seed9900 \
  --input-run runs/m133_zero_relvel_s60_strict_60ep_seed9920 \
  --deduplicate \
  --run-dir runs/m136_m133_proof_surface_retention_corpus
```

Output:

| Metric | Value |
| --- | ---: |
| Input runs | 2 |
| Input rows | 31 |
| Output rows | 20 |
| Duplicate rows removed | 11 |
| Unique seeds | 9 |
| Weight sum | 0.150278 |
| Weight min | 0.002593 |
| Weight max | 0.021283 |

Source condition coverage remains perturbed-only:

| Source condition | Rows |
| --- | ---: |
| perturbed | 20 |

Primary source-run counts:

| Source run | Rows |
| --- | ---: |
| `runs/m133_zero_relvel_s60_strict_60ep_seed9900` | 17 |
| `runs/m133_zero_relvel_s60_strict_60ep_seed9920` | 3 |

## M62 Control Cleanliness

The M133 M62 controls remain clean under the same strict profile:

| Run | Accepted outcome rows | Selected pairs | Selected seeds | Exported snippets |
| --- | ---: | ---: | ---: | ---: |
| M62 seed9900 | 0 | 0 | 0 | 0 |
| M62 seed9920 | 0 | 0 | 0 | 0 |

## Retention Coverage Audit

M136 also writes:

- `runs/m136_m133_proof_surface_retention_corpus/retention_coverage.csv`
- `runs/m136_m133_proof_surface_retention_corpus/retention_summary.json`

The audit compares the 11 unique M133 snippet keys
`(seed, source_condition, source_step, paired_step)` against M134/M135 strict
exports.

| Candidate run | Retained keys | Lost keys | Coverage |
| --- | ---: | ---: | ---: |
| M134 final seed9900 | 7 | 4 | 0.636 |
| M134 final seed9920 | 7 | 4 | 0.636 |
| M134 step4096 seed9900 | 8 | 3 | 0.727 |
| M134 step4096 seed9920 | 8 | 3 | 0.727 |
| M135 s2048 a1 seed9900 | 8 | 3 | 0.727 |
| M135 s2048 a1 seed9920 | 8 | 3 | 0.727 |
| M135 s2048 a20 seed9900 | 8 | 3 | 0.727 |
| M135 s2048 a20 seed9920 | 8 | 3 | 0.727 |
| M135 s4096 a20 seed9900 | 8 | 3 | 0.727 |
| M135 s4096 a20 seed9920 | 8 | 3 | 0.727 |

This explains why behavior gates alone were misleading: later PPO candidates
keep the same aggregate success and visible zero-response gap, but they do not
retain all of the M133 proof-surface keys.

## Decision

The M133 retention corpus is ready for objective-sanity work, not driver
promotion.

The next experiment should optimize or gate directly against the M136 corpus
before PPO resumes. The source-side limitation remains important: the corpus is
still perturbed-source only.

## Next Step

M137 should run an objective-only sanity update from M132 s60 using the M136
corpus and then rerun M133-style behavior and strict proof-surface gates.
