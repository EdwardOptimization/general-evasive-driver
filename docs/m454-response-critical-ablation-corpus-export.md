# M454 Response-Critical Ablation Corpus Export

## Purpose

M454 implements the M453 response-critical corpus design. It exports structured
ablation rows from M452 near/late robust benchmark episodes, separating:

- dependency class: current-response, recurrent-hidden, action-history, mixed,
  or weak behavior shift;
- failure class: obstacle collision/margin crossing, near-boundary obstacle
  margin, road-boundary failure, stability/return shift, clearance shift, or
  ablation rescue.

This milestone does not train or promote a checkpoint and does not change actor
inputs.

## Implementation

Added:

```text
src/autodrift/response_critical_ablation_corpus.py
tests/test_response_critical_ablation_corpus.py
```

The exporter writes:

```text
candidates.csv
compact_corpus.csv
summary.json
```

The exported columns include source config, seed, ablation policy, dependency
class, failure class, divergence types, clearance/return/lateral/beta deltas,
obstacle label, mu bucket, and hidden-condition metadata for diagnostics only.
These fields are not actor inputs.

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_response_critical_ablation_corpus.py
```

Result:

```text
3 passed
```

## Export Command

```bash
PYTHONPATH=src python -m autodrift.response_critical_ablation_corpus \
  --episodes-csv runs/m452_near_robust_ablation_seed9900/episodes.csv \
  --source-config near_robust \
  --track-width 8.2 \
  --episodes-csv runs/m452_late_robust_ablation_seed9900/episodes.csv \
  --source-config late_robust \
  --track-width 8.0 \
  --baseline-policy m399_base \
  --candidate-policy m399_reset \
  --candidate-policy m399_zero_current \
  --candidate-policy m399_zero_all \
  --candidate-policy m399_noact \
  --run-dir runs/m454_response_critical_ablation_corpus
```

## Summary

Run directory:

```text
runs/m454_response_critical_ablation_corpus
```

Core counts:

| metric | value |
| --- | ---: |
| rows compared | `1024` |
| accepted rows | `685` |
| compact rows | `86` |
| max config dominance | `0.500000` |
| max policy dominance | `0.279070` |
| max failure-class dominance | `0.372093` |
| max obstacle-label dominance | `0.372093` |

Selected compact rows by source:

| source config | rows |
| --- | ---: |
| late_robust | `43` |
| near_robust | `43` |

Selected compact rows by policy:

| policy | rows |
| --- | ---: |
| m399_noact | `14` |
| m399_reset | `24` |
| m399_zero_all | `24` |
| m399_zero_current | `24` |

Selected compact rows by dependency class:

| dependency class | rows |
| --- | ---: |
| action_history_sensitive | `3` |
| current_response_sensitive | `2` |
| mixed_dependency | `79` |
| recurrent_hidden_sensitive | `2` |

Selected compact rows by failure class:

| failure class | rows |
| --- | ---: |
| ablation_rescue | `1` |
| clearance_margin_shift | `32` |
| near_boundary_obstacle_margin | `32` |
| obstacle_collision_margin_crossing | `4` |
| return_only_shift | `7` |
| road_boundary_failure | `10` |

Selected compact rows by obstacle label:

| obstacle label | rows |
| --- | ---: |
| aes_feasible | `22` |
| drift_required | `32` |
| unavoidable | `32` |

Selected compact rows by mu bucket:

| mu bucket | rows |
| --- | ---: |
| high | `28` |
| low | `32` |
| medium | `26` |

Selected compact divergence counts:

| divergence type | rows |
| --- | ---: |
| beta_peak_delta | `10` |
| collision_flip | `5` |
| large_margin_delta | `71` |
| lateral_boundary_flip | `10` |
| lateral_peak_delta | `24` |
| margin_sign_flip | `5` |
| near_boundary_margin_delta | `37` |
| return_delta | `65` |
| success_flip | `15` |

## Interpretation

M454 upgrades M452 from aggregate ablation tables to an interpretable corpus.
The compact corpus is source-diverse across near/late configs, ablation
policies, obstacle labels, and mu buckets.

Evidence quality is `moderate`, not `strong`:

- The corpus contains real response-critical rows, including `15` selected
  success flips and `5` selected collision/margin sign flips.
- It is not dominated by one config or one policy.
- However, selected rows are mostly `mixed_dependency` because the same seeds
  often diverge under more than one ablation.
- Standalone recurrent-hidden and action-history evidence remains sparse:
  `2` selected recurrent-hidden rows and `3` selected action-history rows.

The correct next step is not training. The correct next step is a multi-seed
expansion to see whether standalone recurrent/action-history rows remain sparse
or whether M452 seed `9900` was just too small.

## Decision

M454 passes as an infrastructure/generalization export. It admits:

```text
m455-response-critical-multiseed-expansion
```

M455 should run the same ablation benchmark over additional M451 robust seed
blocks and re-export a combined corpus. It should decide whether the evidence is
strong enough for a future self-ID gate or weak enough to redirect to task-family
redesign.
