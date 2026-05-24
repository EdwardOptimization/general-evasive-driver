# M635 Combined Source-7 Preserving Shape Design

## Purpose

M635 designs a no-training combined projected shape search after M634.

Question:

```text
Can we keep M633's source8/source0/source30 gains while restoring source7,
without widening trust regions or lowering thresholds?
```

This is design-only:

```text
no rollout
no training
no PPO
no checkpoint promotion
no optimizer admission
no trust-region relaxation
no target-threshold relaxation
```

## Parent Evidence

M633 result:

| Source | M630 accepted | M633 accepted | Best M633 improvement | Status |
| ---: | ---: | ---: | ---: | --- |
| `8` | `0` | `664` | `0.026789` | recovered |
| `0` | `0` | `196` | `0.022995` | recovered |
| `30` | `4` | `430` | `0.029507` | preserved |
| `7` | `5` | `0` | `0.019965` | regressed |

M634 diagnosis:

```text
source7 regression is grid_coverage_regression
```

M633 did not include the source-7 M630 success pattern:

```text
steer_delta: around 0.08
throttle_delta: around 0.00
brake_delta: 0.00 or 0.04
```

## Design Principle

Do not create one large global Cartesian grid. That would inflate candidate
count and make interpretation harder.

Instead, M636 should run two named grid groups:

```text
source8_recovery_grid
source7_preservation_grid
```

The result should be a union of accepted candidates from both groups, with
`grid_name` recorded on every candidate row.

## Grid Group A: Source8 Recovery

Use the M633 source8/source0/source30 grid:

```text
source_ids: 8, 0, 30
sequence_lengths: 5, 7, 9
families:
  targeted_constant_delta
  targeted_decay_hold
  targeted_late_brake_hold
  targeted_steer_build_brake_hold
  targeted_smoothstep_hold

steer_deltas:
  -0.02, 0.00, 0.02, 0.03, 0.04, 0.05, 0.06

throttle_deltas:
  -0.08, -0.07, -0.06, -0.05

brake_deltas:
  0.02, 0.03, 0.04, 0.05, 0.06, 0.08
```

This grid should preserve M633's source `8`, `0`, and `30` gains.

## Grid Group B: Source7 Preservation

Use a compact grid around M630's source-7 pattern:

```text
source_ids: 7
sequence_lengths: 3, 5, 7, 9
families:
  targeted_constant_delta
  targeted_decay_hold
  targeted_late_brake_hold

steer_deltas:
  0.06, 0.08, 0.10

throttle_deltas:
  -0.02, 0.00, 0.02

brake_deltas:
  0.00, 0.02, 0.04
```

Every raw candidate must still be projected back into:

```text
sequence_mean_l2 <= 0.08
sequence_max_l2 <= 0.10
max_delta_delta_l2 <= 0.08
```

## Implementation Shape

M636 should add a small combined runner rather than overloading one global grid:

```text
src/autodrift/combined_projected_sequence_shape.py
```

It can reuse:

```text
targeted_projected_sequence_shape.run_targeted_projected_sequence_shape
trust_projected_sequence_shape projection and rollout helpers
```

But the final artifact should combine both grid groups into one source-level
summary.

## Required Artifacts

M636 should write:

```text
runs/m636_combined_source7_preserving_shape/combined_projected_candidates.csv
runs/m636_combined_source7_preserving_shape/accepted_combined_sequences.csv
runs/m636_combined_source7_preserving_shape/source_recovery_summary.csv
runs/m636_combined_source7_preserving_shape/summary.json
docs/m636-combined-source7-preserving-shape-implementation.md
```

Required summary keys:

```text
source8_recovered
source0_recovered
source7_recovered
source30_preserved
all_four_sources_have_acceptance
trust_limits_preserved
candidate_rollouts
accepted_combined_candidates
accepted_counts_by_source
accepted_counts_by_grid
```

## Interpretation Rules

Positive diagnostic:

```text
source8_recovered == true
source0_recovered == true
source7_recovered == true
source30_preserved == true
trust_limits_preserved == true
```

Strong positive diagnostic:

```text
all_four_sources_have_acceptance == true
accepted sources cover both fresh and ood surfaces
accepted targets include future_yaw_response and future_braking_deceleration
```

Still not automatic optimizer admission:

```text
even if all four sources pass, M637 must audit breadth and overfitting before
any target-corpus or actor-update decision
```

Negative diagnostic:

```text
source7 remains below threshold or source8/source0/source30 regress
```

## Contract Checks

```text
actor_input_changed: false
labels_enter_actor_input: false
actor_parameters_changed: false
ppo_used: false
promoted: false
optimizer_admission: false
target_acceptance_thresholds_changed: false
trust_regions_changed: false
```

## Decision

Decision:

```text
combined_source7_preserving_shape_design_admit_m636
```

Next blocker:

```text
m636-combined-source7-preserving-shape-implementation
```
