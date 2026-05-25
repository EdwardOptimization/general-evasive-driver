# M791 V4 Residual Component Sensitivity Design

## Purpose

M791 designs a no-training component sensitivity probe after M790 audited the
M789 vector gate as a clean component-collapse negative.

The question is:

```text
Which M761 residual action components create intervention benefit, and which
components create active-source normal collision risk?
```

This milestone is design-only:

```text
no implementation
no replay run
no optimizer run
no actor update
no residual-head update
no PPO
no checkpoint promotion
```

## Motivation

M789 showed that simply changing the gate output from 1 dimension to 3
dimensions is not enough:

```text
normal gate components:
  steer/throttle/brake = 0.671292 / 0.671167 / 0.671190

intervention gate components:
  steer/throttle/brake = 0.684914 / 0.684800 / 0.684820

gate_component_std_mean:
  0.000066
```

This is effectively scalar behavior. The missing evidence is component
attribution:

```text
Does steer residual cause the active normal collision?
Does brake residual provide most intervention gap?
Does throttle residual matter?
Do combinations matter?
```

M792 should answer those questions with fixed masks, not training.

## Actor Contract

The deployable actor contract does not change:

```text
P0 human-view no-wheel 72-dim frame + online GRU hidden state
```

M792 uses:

```text
frozen M568 actor
frozen M761 residual head
fixed residual masks
```

Forbidden:

```text
no hidden parameters as actor input
no terminal margin as actor input
no fault labels as deploy-time input
no learned calibrator
no PPO
no promotion
```

Fault labels and terminal margins may only appear in logs and stratified audit
tables.

## Component Masks

M792 should evaluate fixed residual masks:

```text
none:              [0, 0, 0]
all:               [1, 1, 1]

steer_only:        [1, 0, 0]
throttle_only:     [0, 1, 0]
brake_only:        [0, 0, 1]

no_steer:          [0, 1, 1]
no_throttle:       [1, 0, 1]
no_brake:          [1, 1, 0]

steer_throttle:    [1, 1, 0]
steer_brake:       [1, 0, 1]
throttle_brake:    [0, 1, 1]
```

`no_throttle` and `steer_brake` are the same vector, and `no_steer` and
`throttle_brake` are the same vector. The implementation may either preserve
both aliases for readability or de-duplicate masks while writing aliases in
metadata.

Executed action:

```text
delta_raw = frozen M761 residual_head(feature)
delta_masked = mask * delta_raw
action = frozen_base_action + alpha * delta_masked
```

This is not a controller rule. It is an audit-only attribution probe over the
already learned M761 residual.

## Alpha Ladder

M792 should evaluate:

```text
alpha: 0.0, 0.125, 0.15, 0.2
```

Primary diagnostic:

```text
alpha 0.2
```

Reason:

```text
alpha 0.2 has the strongest intervention gap but fails strict normal retention
on the active source. Component attribution should explain that failure before
another learned vector objective is attempted.
```

## Data

Use the same broader corpus:

```text
runs/m773_v4_broader_source_holdout_corpus_export/positive_sequence_outcomes.csv
runs/m773_v4_broader_source_holdout_corpus_export/contrast_rows.csv
configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json
```

Reference artifacts:

```text
runs/m780_v4_broader_normal_boundary_alpha_probe/alpha_metrics.csv
runs/m786_v4_asymmetric_residual_gate/alpha_metrics.csv
runs/m789_v4_vector_residual_calibration/alpha_metrics.csv
```

The active source must be stratified:

```text
seed: 77025
source_index: 12
step: 24
fault_family_pair: drive_authority_drop->rear_lateral_authority_drop
```

## Required Metrics

M792 should write:

```text
summary.json
mask_alpha_metrics.csv
component_replay_rows.csv
component_objective_rows.csv
active_source_metrics.csv
rejected_rows.csv
```

For every `mask_name, alpha`:

```text
normal_success_rate
normal_collision_rate
strict_normal_retention_pass
intervention_action_gap_mean
intervention_action_gap_p10
normal_minus_intervention_margin_gap_mean
outcome_sensitivity_retention_rate
active_source_min_margin
active_source_collision_count
normal_first_action_drift_mean_vs_base
residual_l2_mean_by_component
```

Active-source table should include:

```text
mask_name
alpha
normal_margin
normal_collision
intervention_margin_by_variant
first_raw_residual_steer/throttle/brake
first_masked_residual_steer/throttle/brake
first_action_steer/throttle/brake
```

## Attribution Criteria

M792 should classify component roles.

### Harmful Component Evidence

A component is harmful if:

```text
all @ alpha 0.2 collides on the active source
and no_component @ alpha 0.2 restores strict normal retention
and component_only @ alpha 0.2 recreates a large fraction of active margin loss
```

Use the active source as the primary diagnostic, then confirm aggregate normal
retention over the corpus.

### Useful Component Evidence

A component is useful if:

```text
component_only or combination mask improves intervention gap over base
and preserves outcome_sensitivity_retention_rate >= 0.95
```

### Actionable Pareto Evidence

A mask is actionable if:

```text
strict normal retention passes
and intervention_gap_mean > M786 alpha 0.15 gap mean
and active_source_min_margin >= M786 alpha 0.15 active margin
```

References:

```text
M786 alpha 0.15 gap mean: 0.043397390743
M786 alpha 0.15 active margin: +0.000028245983
M780 alpha 0.125 gap mean: 0.044046541597
```

If a mask at alpha `0.2` meets the stronger M780 gap reference while preserving
active-source margin, it should be marked as `component_actionable_pareto`.

## Result Classes

M792 should classify:

```text
v4_residual_component_sensitivity_actionable_pareto:
  at least one mask is strict-normal-safe and beats M786 alpha 0.15 on both
  gap and active-source margin

v4_residual_component_sensitivity_attribution_found:
  no actionable mask, but harmful/useful components are clearly identified

v4_residual_component_sensitivity_no_component_signal:
  no mask explains active-source collision or intervention gap lift

v4_residual_component_sensitivity_replay_blocked:
  reconstruction or replay fails

v4_residual_component_sensitivity_metadata_artifact:
  actor/residual mutation, PPO, promotion, or metadata contamination occurs
```

## Implementation Guardrails

M792 must:

```text
freeze base actor;
freeze M761 residual head;
use fixed masks only;
record actor and residual checksums before and after;
write per-mask and active-source tables;
preserve unsupported-variant rejection reporting;
avoid training;
avoid PPO;
avoid promotion.
```

M792 must not:

```text
learn mask values;
train a calibrator;
change actor inputs;
hide active-source failures;
claim broad generalization;
claim true four-wheel or per-wheel physical fidelity.
```

## Decision

M791 admits one implementation milestone:

```text
m792-v4-residual-component-sensitivity-implementation
```

If M792 finds actionable component attribution, the next branch can design a
component-attributed vector objective. If it does not, residual calibration
should stop or pivot back to corpus/architecture evidence rather than tuning
another gate blindly.
