# M275 Terminal-Margin Retention Surface Export

M275 implements and runs a current-base terminal-margin retention surface export
before any further actor update or PPO.

No PPO, actor update, promotion, or actor-input change was performed.

## Implementation

Added:

```text
src/autodrift/terminal_margin_retention_surface.py
```

The exporter reads selected replay rows, selects fragile rows, reconstructs the
current policy's normal continuation, and writes an existing
`TrajectoryActionAnchor`-compatible NPZ.

Selection rule:

```text
candidate policy = m272b_a0_01025
normal_success == true
success_drop == true
0 < normal_margin <= 0.001
force include m183_m170:16
```

Retention weighting:

```text
weight = clamp(max_normal_margin / max(normal_margin, weight_epsilon), 1, 50)
```

The terminal-margin registry stores:

```text
normal_margin
wrong_history_margin
margin_gap
hard_floor
allowed_regression
required_margin_floor
retention_weight
```

## Export

Command output directory:

```text
runs/m275_terminal_margin_retention_surface
```

Artifacts:

```text
runs/m275_terminal_margin_retention_surface/fragile_rows.csv
runs/m275_terminal_margin_retention_surface/terminal_margin_registry.csv
runs/m275_terminal_margin_retention_surface/retention_trajectory_anchor.npz
runs/m275_terminal_margin_retention_surface/retention_trajectory_anchor.csv
runs/m275_terminal_margin_retention_surface/recovery_trajectory_anchor_unavailable.json
runs/m275_terminal_margin_retention_surface/summary.json
```

Summary:

| Metric | Value |
| --- | ---: |
| fragile rows | 30 |
| trajectory anchor rows | 1440 |
| required row16 present | true |
| weight min | 1.011909 |
| weight max | 50.000000 |
| weight mean | 3.551724 |

Fragile row coverage:

| Surface | Rows |
| --- | ---: |
| M183 M168 | 13 |
| M183 M170 | 14 |
| M193 M189 | 3 |
| M212 M204 | 0 |
| M223 M219 | 0 |
| M267 M264 | 0 |

M183/M170 row16 is included with:

| Field | Value |
| --- | ---: |
| normal margin | 0.000000636 |
| wrong-history margin | -0.005949 |
| margin gap | 0.005950 |
| allowed regression | 0.000000500 |
| required margin floor | 0.000000136 |
| retention weight | 50.000000 |

## Anchor Validation

The retention NPZ loads through the existing trajectory anchor loader:

```text
observation        1440 x 72
hidden             1440 x 128
reference_action   1440 x 3
source_index       1440
step_index         1440
weight             1440
```

The exported anchor is therefore directly usable by
`outcome_intervention_optimize --trajectory-action-anchor-snapshot-npz`.

## Recovery Anchor

M275 does not export a recovery trajectory anchor.

Reason:

```text
Recovery anchors from older source policies are not exported in M275 because
recurrent hidden states are checkpoint-specific. A future recovery anchor must
align source actions to the current checkpoint hidden state before training.
```

This keeps the actor-input contract clean and avoids feeding a current actor
hidden states from an unrelated checkpoint.

## Validation

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_terminal_margin_retention_surface.py \
  tests/test_intervention_objectives.py \
  tests/test_outcome_intervention_optimize.py
```

Result:

```text
19 passed in 2.16s
```

## Decision

M275 completes the retention surface export.

Decision:

```text
admit_terminal_margin_anchored_actor_update
```

Next step:

```text
m276-terminal-margin-anchored-actor-update
```

M276 may run exactly one small actor-coupling update from `m272b_a0_01025` using
the M270 source-balanced objective plus the M275 retention trajectory anchor.
It must gate row16 terminal margin before any broader replay, behavior, or
promotion check. PPO remains blocked.
