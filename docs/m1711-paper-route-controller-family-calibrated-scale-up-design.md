# M1711 Paper-Route Controller-Family Calibrated Scale-Up Design

- status: completed
- decision: `calibrated_scale_up_design_admit_no_rollout_preflight`
- parent synthesis: `docs/m1710-paper-route-controller-family-task-quality-calibration-branch-synthesis.md`

## Summary

M1711 designs a source-expanded calibrated scale-up while keeping the execution
budget fixed at `864` episodes.

This milestone is design-only. It does not execute rollout, train, replay, run
PPO, promote, use private holdout, change actor inputs, tune profiles, or claim
controller-family ranking, paper-level evidence, or level3 self-identification.

## Design Goal

M1708/M1709 found that the best bounded-smoke variant reduced off-track
dominance, but also increased collision rate. M1711 therefore must not scale
only the best off-track variant.

The scale-up should answer:

```text
Does the task-quality calibration signal survive broader source coverage while
preserving the collision/off-track tradeoff?
```

It should not answer:

```text
Which controller-family profile is best?
```

## Fixed-Budget Shape

M1712 should materialize a no-rollout scale-up subset:

```text
selected base specs: 18
task split: T4=9, T5=9
calibration variants per base spec: 4
profiles: 12
total cells: 18 * 4 * 12 = 864
```

This expands source coverage from the M1705 six-base-spec smoke without
increasing the measured execution budget.

## Base-Spec Selection Rule

M1712 should start with the six M1705 selected base specs as anchors:

```text
m1680-spec-0000
m1680-spec-0001
m1680-spec-0006
m1680-spec-0036
m1680-spec-0039
m1680-spec-0040
```

Then add `12` more base specs from the full M1702 matrix:

```text
additional T4 specs: 6
additional T5 specs: 6
```

Use deterministic greedy source diversity, preferring distinct:

```text
source_edge;
executable_source_family;
env_template_family;
window_tag.
```

If candidates tie, use lexical `base_task_source_id`. The preflight must write
both selected and rejected base specs with selection/rejection reasons.

## Calibration Variant Panel

For every selected base spec, keep exactly four variants:

| label | track width | finish | max steps | reason |
| --- | ---: | --- | ---: | --- |
| `original_axis_baseline` | `1.0` | `original` | `1.0` | preserves the M1707 baseline |
| `best_off_track_variant` | `2.0` | `original` | `1.5` | M1709 best off-track result |
| `collision_control_wide_relaxed` | `2.0` | `relaxed` | `1.0` | checks whether wide track can avoid higher collision cost |
| `mid_calibration_variant` | `1.5` | `relaxed` | `1.5` | tests a less extreme calibrated setting |

The exact labels should be written into the scale-up matrix so later audit can
compare variants without reconstructing them from raw axes.

## Required Controls

Every selected calibration spec must keep all twelve controller-family profiles:

```text
L0_current_masked
L1_one_step
L2_window_13
L2_window_13_current_tiled
L2_window_25
L2_window_25_current_tiled
L2_window_50
L2_window_50_current_tiled
L2_window_100
L2_window_100_current_tiled
L3_online_gru
L3_reset_control_corrected
```

Profile rows remain controls and diagnostics. M1712/M1713 must not rank profiles.

## M1712 Preflight Artifacts

M1712 should write:

```text
runs/m1712_controller_family_calibrated_scale_up_preflight/summary.json
runs/m1712_controller_family_calibrated_scale_up_preflight/selected_base_specs.csv
runs/m1712_controller_family_calibrated_scale_up_preflight/rejected_base_specs.csv
runs/m1712_controller_family_calibrated_scale_up_preflight/scale_up_calibration_specs.json
runs/m1712_controller_family_calibrated_scale_up_preflight/scale_up_calibration_specs.csv
runs/m1712_controller_family_calibrated_scale_up_preflight/scale_up_matrix.csv
runs/m1712_controller_family_calibrated_scale_up_preflight/contract_violations.csv
```

Expected no-rollout counts:

```text
selected base specs: 18
selected task family counts: T4=9, T5=9
scale-up calibration specs: 72
scale-up matrix cells: 864
profile count: 12
contract violations: 0
environment rollout started: false
```

## Later Execution Audit Rules

A later execution audit should compare:

```text
best_off_track_variant vs original_axis_baseline;
collision_control_wide_relaxed vs best_off_track_variant;
mid_calibration_variant vs both extremes;
T4 vs T5 task-family stability;
source-edge stability.
```

Scale-up should be considered useful only if:

```text
best_off_track_variant or mid_calibration_variant improves off-track rate
without unacceptable collision growth across broader sources;
and at least one calibrated variant remains below the M1707 0.70 off-track
interpretability threshold or clearly improves over baseline by >= 0.10.
```

The exact threshold for "unacceptable collision growth" should be pre-registered
in the later execution design after M1712/M1713 confirm the subset.

## Decision

Admit M1712 no-rollout calibrated scale-up preflight. Do not execute the
scale-up until the subset is materialized, audited, and explicitly routed to a
measured execution milestone.
