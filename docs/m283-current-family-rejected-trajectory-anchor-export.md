# M283 Current-Family Rejected-Trajectory Anchor Export

M283 implements and runs the current-family rejected-history trajectory anchor
export designed in M282.

No PPO, actor update, promotion, or actor-input change was performed.

## Setup

Current base checkpoint:

```text
runs/m272_m264_to_m271_interpolation_boundary/checkpoints/alpha_0_01025.pt
```

Current-family corpus:

```text
runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
```

Base normal retention/recovery anchor:

```text
runs/m279_combined_retention_recovery_anchor/combined_trajectory_anchor.npz
```

## Implementation

Added:

```text
src/autodrift/rejected_history_trajectory_anchor.py
tests/test_rejected_history_trajectory_anchor.py
```

The exporter reconstructs M272 current-base snapshots, relocates the obstacle
to the registered boundary geometry, starts each rollout from the matched
wrong-history hidden state, and records the rejected-history observation,
hidden, and reference action at each continuation step.

It does not use old checkpoint hidden states.

## Export

Run directory:

```text
runs/m283_current_family_rejected_trajectory_anchor
```

Artifacts:

```text
runs/m283_current_family_rejected_trajectory_anchor/rejected_trajectory_anchor.npz
runs/m283_current_family_rejected_trajectory_anchor/rejected_trajectory_anchor.csv
runs/m283_current_family_rejected_trajectory_anchor/combined_recovery_rejected_anchor.npz
runs/m283_current_family_rejected_trajectory_anchor/summary.json
```

Export settings:

| Setting | Value |
| --- | ---: |
| M267/M264 rows selected | 17 |
| forced failed rows | 4, 6, 11, 13, 15, 16 |
| max continuation steps | 60 |
| rejected weight | 10 |
| failed-row weight | 50 |
| rejected repeat in combined anchor | 16 |

Rejected anchor:

| Metric | Value |
| --- | ---: |
| rows | 669 |
| observation shape | 669 x 72 |
| hidden shape | 669 x 128 |
| reference action shape | 669 x 3 |
| weight min | 10.000000 |
| weight max | 50.000000 |
| weight mean | 24.409567 |

Combined anchor:

| Metric | Value |
| --- | ---: |
| base rows | 1890 |
| rejected rows before repeat | 669 |
| rejected repeat | 16 |
| combined rows | 12594 |
| observation shape | 12594 x 72 |
| hidden shape | 12594 x 128 |
| reference action shape | 12594 x 3 |
| weight mean | 21.267803 |

Rows per M267/M264 row id:

| Row id | Trajectory rows |
| ---: | ---: |
| 0 | 46 |
| 1 | 46 |
| 2 | 30 |
| 3 | 30 |
| 4 | 43 |
| 5 | 43 |
| 6 | 40 |
| 7 | 40 |
| 8 | 37 |
| 9 | 40 |
| 10 | 43 |
| 11 | 29 |
| 12 | 37 |
| 13 | 46 |
| 14 | 36 |
| 15 | 34 |
| 16 | 49 |

## Validation

Both exported NPZ files load through `load_trajectory_action_anchor`:

```text
rejected_trajectory_anchor.npz:
  rows = 669
  observation = 669 x 72
  hidden = 669 x 128
  reference_action = 669 x 3

combined_recovery_rejected_anchor.npz:
  rows = 12594
  observation = 12594 x 72
  hidden = 12594 x 128
  reference_action = 12594 x 3
```

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_rejected_history_trajectory_anchor.py \
  tests/test_terminal_margin_recovery_anchor.py \
  tests/test_intervention_objectives.py
```

Result:

```text
20 passed in 2.18s
```

## Decision

M283 completes the current-family rejected-history trajectory anchor export.

Decision:

```text
admit_rejected_trajectory_anchored_update
```

Next step:

```text
m284-rejected-trajectory-anchored-update
```

M284 may run one small no-PPO actor-coupling update from M272 using the M283
combined recovery/rejected anchor. It must gate M183/M170 row16 and M267/M264
before any broader proof gates. PPO remains blocked.
