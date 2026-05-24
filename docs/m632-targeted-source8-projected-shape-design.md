# M632 Targeted Source-8 Projected Shape Design

## Purpose

M632 designs a no-training source-8 targeted projected shape search after M631.

Question:

```text
Can a local projected candidate-shape search recover source 8 without changing
trust limits or margin/risk thresholds?
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

M630 source recovery:

| Source | Before | After | Best improvement | Status |
| ---: | ---: | ---: | ---: | --- |
| `30` | `0` | `4` | `0.021397` | recovered |
| `7` | `3` | `5` | `0.020817` | improved |
| `8` | `0` | `0` | `0.018752` | near threshold |
| `0` | `0` | `0` | `0.015290` | below threshold |

Source `8` details:

```text
tier: core_boundary
surface: ood
target: future_yaw_response
variant: delayed_history
accepted_before_m624: 0
best_projected_margin_improvement: 0.018752
margin gap to threshold: 0.001248
```

Top source-8 candidates from M630 are all K=7 projected constant-delta rows:

| Improvement | Steer | Throttle | Brake | Scale |
| ---: | ---: | ---: | ---: | ---: |
| `0.018752` | `0.04` | `-0.06` | `0.04` | `0.970142` |
| `0.018720` | `0.00` | `-0.06` | `0.04` | `1.000000` |
| `0.017718` | `0.00` | `-0.06` | `0.08` | `0.799999` |
| `0.017575` | `-0.04` | `-0.06` | `0.04` | `0.970142` |

The local pattern is:

```text
sequence_length: K=7
family: constant_delta
throttle_delta: -0.06
steer_delta: near 0.00 to 0.04
brake_delta: near 0.04
```

## Target Sources

M633 should focus:

```text
primary source: 8
secondary source: 0
regression sentinels: 7 and 30
```

Source `8` is the only primary recovery target. Source `0` is secondary because
it remains farther below threshold. Sources `7` and `30` should be included only
to make sure the targeted shape pass does not lose already recovered projected
evidence.

Collision-primary sources remain excluded.

## Local Candidate Grid

M633 should use a local microgrid around source-8 best signs:

```text
steer_deltas:
  -0.02, 0.00, 0.02, 0.03, 0.04, 0.05, 0.06

throttle_deltas:
  -0.08, -0.07, -0.06, -0.05

brake_deltas:
  0.02, 0.03, 0.04, 0.05, 0.06, 0.08
```

Sequence lengths:

```text
K=5
K=7
K=9
```

K=9 is allowed because it does not relax per-step or sequence trust limits; it
only tests whether a longer low-amplitude prefix can carry the same maneuver
more smoothly.

## Shape Families

M633 should include:

```text
targeted_constant_delta
targeted_decay_hold
targeted_late_brake_hold
targeted_steer_build_brake_hold
targeted_smoothstep_hold
```

Implementation rule:

```text
all families produce raw delta_sequence
raw delta_sequence is radially projected into the existing trust limits
rollout uses only projected candidate actions
```

The families should stay action-native:

```text
steer / throttle / brake
```

Do not introduce reference paths, acceleration commands, feasibility labels, or
rule-mode outputs.

## Required Artifacts

M633 should write:

```text
runs/m633_targeted_source8_projected_shape/targeted_projected_candidates.csv
runs/m633_targeted_source8_projected_shape/accepted_targeted_sequences.csv
runs/m633_targeted_source8_projected_shape/source_recovery_summary.csv
runs/m633_targeted_source8_projected_shape/summary.json
docs/m633-targeted-source8-projected-shape-implementation.md
```

Required summary keys:

```text
source8_recovered
source8_best_margin_improvement
source0_best_margin_improvement
source7_regression
source30_regression
trust_limits_preserved
candidate_rollouts
accepted_targeted_candidates
accepted_counts_by_source
```

## Interpretation Rules

Positive diagnostic:

```text
source8_recovered == true
trust_limits_preserved == true
source7_regression == false
source30_regression == false
```

Weak positive diagnostic:

```text
source8_best_margin_improvement improves but remains below 0.02
```

Negative diagnostic:

```text
source8 does not improve over M630 or targeted shapes regress sources 7 or 30
```

Even a positive source-8 result is not automatic optimizer admission. It should
go through M634 audit because source-level breadth would still be small.

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
targeted_source8_projected_shape_design_admit_m633
```

Next blocker:

```text
m633-targeted-source8-projected-shape-implementation
```
