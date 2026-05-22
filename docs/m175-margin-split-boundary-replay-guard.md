# M175 Margin-Split Boundary Replay Guard

M174 showed that the rows lost by M170 and M171 are knife-edge rows under the
admitted M168 checkpoint. M175 turns that split into a reusable guard and
evaluates M168, M170, and M171 under robust, watchlist, and knife-edge classes.

This is a positive harness result. M170 passes robust-row retention and behavior
checks, but still loses knife-edge row `67`, so it is not a strict full-replay
replacement for M168.

## Added Guard

Added:

```text
src/autodrift/boundary_margin_split_replay_guard.py
tests/test_boundary_margin_split_replay_guard.py
```

The guard:

- classifies success-drop rows under a class-reference policy;
- uses `robust_threshold=0.001` and `knife_edge_threshold=0.0005`;
- treats robust-row retention as the hard gate;
- reports watchlist and knife-edge losses separately.

Focused test:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_boundary_margin_split_replay_guard.py tests/test_boundary_fragile_row_guard.py
```

Result:

```text
8 passed
```

## Split Classes

Class reference:

```text
runs/m168_from_m167_5168_boundary_outcome_replay_gate_seed9510/boundary_replay_rows.csv
m168_from_m167_5168
```

| Class | Rows |
| --- | --- |
| robust | `[6, 7, 9, 10, 11, 12, 15, 33, 41, 48, 54]` |
| watchlist | `[17, 56]` |
| knife-edge | `[67, 70, 77]` |

## Candidate Results

| Candidate | Robust lost | Watchlist lost | Knife-edge lost | Split gate |
| --- | --- | --- | --- | --- |
| m168_from_m167_5168 | `[]` | `[]` | `[]` | pass |
| m170_stage2 | `[]` | `[]` | `[67]` | pass |
| m171_s512_a100 | `[]` | `[]` | `[70, 77]` | pass |

Under the split, both M170 and M171 preserve all robust promotion rows. M170 is
the stronger candidate because it has the best fixed objective and loses one
knife-edge row rather than two.

## M170 Behavior And Protected Key

Because M170 passed robust-row retention, it received behavior and protected-key
evaluation. M171 did not, because it is weaker on fixed objective and loses two
knife-edge rows.

Seed `9503`:

| Policy | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: |
| m163_a100_s20 | 0.8625 | 0.1375 | 1.846266 |
| m170_stage2 | 0.8625 | 0.1375 | 1.846537 |
| m170_stage2_reset | 0.8500 | 0.1500 | 1.841984 |
| m170_stage2_zero_current | 0.8000 | 0.2000 | 1.856378 |
| m170_stage2_zero_all | 0.8000 | 0.2000 | 1.856378 |
| m170_stage2_noact | 0.8625 | 0.1375 | 1.847866 |

Seed `9504`:

| Policy | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: |
| m163_a100_s20 | 0.8625 | 0.1375 | 1.853828 |
| m170_stage2 | 0.8625 | 0.1375 | 1.854103 |
| m170_stage2_reset | 0.8500 | 0.1500 | 1.850130 |
| m170_stage2_zero_current | 0.8000 | 0.2000 | 1.868341 |
| m170_stage2_zero_all | 0.8000 | 0.2000 | 1.868341 |
| m170_stage2_noact | 0.8625 | 0.1375 | 1.856783 |

Protected key:

```text
runs/m175_m170_critical_key_seed9944
```

| Policy | Accepted cases | Pass |
| --- | ---: | --- |
| m163_a100_s20 | 1 / 1 | true |
| m170_stage2 | 1 / 1 | true |

## Decision

M175 is positive as a guard and evaluation harness.

What passed:

- margin-split guard added and tested;
- M168, M170, and M171 evaluated under the split;
- M170 preserves all robust rows and passes behavior/protected-key checks;
- M171 preserves robust rows but is not advanced because it loses more
  knife-edge rows and has weaker fixed objective.

What remains weak:

- M170 still loses knife-edge row `67`;
- M168 remains the strict full-replay checkpoint;
- M170 is only split-admitted and needs broader evaluation before becoming the
  preferred driver checkpoint;
- no-action history remains behavior-neutral.

Decision: admit M170 to a broader split-aware evaluation, but do not replace
M168 as the strict full-replay checkpoint yet.

## Validation

Commands executed:

```text
PYTHONPATH=src python -m pytest -q tests/test_boundary_margin_split_replay_guard.py tests/test_boundary_fragile_row_guard.py
PYTHONPATH=src python -m autodrift.boundary_margin_split_replay_guard ... m168_from_m167_5168
PYTHONPATH=src python -m autodrift.boundary_margin_split_replay_guard ... m170_stage2
PYTHONPATH=src python -m autodrift.boundary_margin_split_replay_guard ... m171_s512_a100
PYTHONPATH=src python -m autodrift.benchmark ... m170_stage2 --seed 9503
PYTHONPATH=src python -m autodrift.benchmark ... m170_stage2 --seed 9504
PYTHONPATH=src python -m autodrift.critical_key_replay_guard ... m170_stage2
```
