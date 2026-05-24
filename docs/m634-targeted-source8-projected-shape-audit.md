# M634 Targeted Source-8 Projected Shape Audit

## Purpose

M634 audits M633 before any optimizer or combined-grid branch.

Question:

```text
Did M633 produce source-diverse optimizer-ready targets, or did it expose a
new local-grid conflict that must be repaired first?
```

Answer:

```text
M633 is a strong no-training diagnostic, but not optimizer-ready. It recovers
sources 8 and 0 and preserves source 30, but source 7 regresses because the
targeted source-8 grid does not include the M630 source-7 success pattern.
```

## Evidence

M633 artifacts:

```text
runs/m633_targeted_source8_projected_shape/summary.json
runs/m633_targeted_source8_projected_shape/source_recovery_summary.csv
runs/m633_targeted_source8_projected_shape/targeted_projected_candidates.csv
docs/m633-targeted-source8-projected-shape-implementation.md
```

## Result

| Source | M630 accepted | M633 accepted | Best M633 improvement | Delta vs M630 | Status |
| ---: | ---: | ---: | ---: | ---: | --- |
| `8` | `0` | `664` | `0.026789` | `+0.008036` | recovered |
| `0` | `0` | `196` | `0.022995` | `+0.007705` | recovered |
| `30` | `4` | `430` | `0.029507` | `+0.008110` | preserved |
| `7` | `5` | `0` | `0.019965` | `-0.000852` | regressed |

M633 passes these gates:

```text
source8_recovered: true
source0 recovered: true
source30_regression: false
trust_limits_preserved: true
training_used: false
ppo_used: false
promoted: false
```

M633 fails the sentinel-retention expectation:

```text
source7_regression: true
```

## Source-7 Regression Diagnosis

M633 source-7 best row:

```text
family: targeted_decay_hold
K: 9
steer_delta: 0.06
throttle_delta: -0.07
brake_delta: 0.04
margin_improvement: 0.019965
```

M630 had source-7 accepted rows from projected constant-delta patterns around:

```text
steer_delta: 0.08
throttle_delta: 0.00
brake_delta: 0.00 or 0.04
K: 3, 5, 7
```

M633 deliberately centered the local grid on source-8:

```text
steer_delta <= 0.06
throttle_delta in {-0.08, -0.07, -0.06, -0.05}
brake_delta >= 0.02
```

So the source-7 regression is best classified as:

```text
grid_coverage_regression
```

It is not evidence that source 7 and source 8 are fundamentally incompatible.
The best source-7 targeted row is only `0.000035` below threshold.

## Decision

Do not admit optimizer training from M633. Candidate count is high, but it is
source-specific and source 7 regressed.

Do not return immediately to broad source mining. The local search recovered
the intended source 8 and secondary source 0, so the branch is productive.

Admit a combined no-training design:

```text
m635-combined-source7-preserving-shape-design
```

M635 should merge:

```text
source8/source0/source30 local target grid from M633
source7 preservation grid from M630
```

The key source-7 preservation grid should include:

```text
steer_deltas: 0.06, 0.08, 0.10
throttle_deltas: -0.02, 0.00, 0.02
brake_deltas: 0.00, 0.02, 0.04
sequence_lengths: 3, 5, 7, 9
```

All candidates must still be projected into the existing trust limits.

## Contract Checks

```text
diagnostic_only: true
labels_enter_actor_input: false
actor_parameters_changed: false
ppo_used: false
promoted: false
optimizer_admission: false
target_acceptance_thresholds_changed: false
trust_regions_changed: false
```

## Final Classification

Classification:

```text
strong_targeted_positive_with_sentinel_grid_regression
```

Decision:

```text
targeted_source8_projected_shape_audit_admit_combined_source7_preserving_design
```

Next branch:

```text
m635-combined-source7-preserving-shape-design
```
