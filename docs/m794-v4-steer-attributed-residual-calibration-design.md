# M794 V4 Steer-Attributed Residual Calibration Design

## Purpose

M794 designs the next no-PPO residual calibration probe after M793 audited
M792 as a clean attribution-only result.

The question is:

```text
Can a steer-attributed calibrator suppress harmful steering residual on
low-normal-margin branches while retaining steering and brake residual signal
where intervention separation is needed?
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

## Evidence From M792/M793

M792 established:

```text
actionable_mask_count: 0
result_class: v4_residual_component_sensitivity_attribution_found
```

At alpha `0.2`:

```text
all residual:
  gap mean: 0.046317
  active margin: -0.000062

steer_only:
  gap mean: 0.044286
  active margin: -0.000049

throttle_brake / no_steer:
  gap mean: 0.042545
  active margin: +0.000112

brake_only:
  gap mean: 0.041748
  active margin: +0.000119

throttle_only:
  gap mean: 0.041170
  active margin: +0.000117
```

Component roles:

```text
steer:    useful true,  harmful true
brake:    useful true,  harmful false
throttle: useful false, harmful false
```

Therefore the next lever is not a generic vector gate. The objective must
explicitly protect the normal branch against steering residual while preserving
steering and brake residual where they create intervention separation.

## Actor Contract

The deployable actor contract does not change:

```text
P0 human-view no-wheel 72-dim frame + online GRU hidden state
```

Allowed deploy-time calibrator input:

```text
same deployable recurrent feature used by the frozen M761 residual head
```

Forbidden deploy-time inputs remain forbidden:

```text
mu
mass / CG / tire / brake / actuator hidden parameters
slip ratio or slip angle
tire force or friction margin
oracle feasibility labels
AEB/AES/drift-required labels
controller mode
TTC
reference trajectory
path error / heading error / curvature
success / collision / progress labels
terminal margin
fault family labels
source id
```

Training-time terminal margins, source ids, fault family, and intervention
variants may only weight losses and produce audit tables.

## Proposed Model

Base components:

```text
base actor:
  runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
  frozen

base residual head:
  runs/m761_v4_sequence_objective_probe/residual_head.pt
  frozen
```

M795 should add the smallest deployable-feature calibrator that directly
matches the M792 evidence:

```text
SteerAttributedResidualGate(feature) -> [g_steer, g_brake]
```

Primary executed residual:

```text
delta_raw = residual_head(feature)
delta_calibrated = [
  g_steer(feature) * delta_raw_steer,
  0.0,
  g_brake(feature) * delta_raw_brake
]

action = base_action + alpha * delta_calibrated
```

Rationale:

```text
steer is the key useful/harmful component;
brake is useful-only and can be retained as a secondary component;
throttle has no meaningful role in M792 and should not receive primary
objective pressure.
```

The implementation may include a secondary diagnostic mode with fixed throttle
gate equal to the M786 scalar gate reference, but the primary result should use
`g_throttle = 0.0` unless fresh evidence changes the throttle role.

Initial gate:

```text
g_steer: 0.85
g_brake: 0.85
```

This keeps residual retention as the default and makes harmful low-margin
normal steering residual the exception.

## Data

Use:

```text
runs/m773_v4_broader_source_holdout_corpus_export/positive_sequence_outcomes.csv
runs/m773_v4_broader_source_holdout_corpus_export/contrast_rows.csv
configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json
runs/m792_v4_residual_component_sensitivity/mask_alpha_metrics.csv
runs/m792_v4_residual_component_sensitivity/component_role_metrics.csv
```

The active source must stay visible:

```text
seed: 77025
source_index: 12
step: 24
fault_family_pair: drive_authority_drop->rear_lateral_authority_drop
```

M795 should reconstruct tensors by replay, not by trusting CSV action values
as complete training tensors.

## Objective Terms

M795 should train only the `SteerAttributedResidualGate` parameters.

### 1. Low-Margin Normal Steering Suppression

For normal-history rows:

```text
low_margin_weight =
  clip((m_cutoff - normal_margin_base) / m_cutoff, 0, 1)^2

L_low_margin_steer =
  low_margin_weight * (g_steer_n * delta_steer_n)^2
```

Initial:

```text
m_cutoff: 0.001
```

Purpose:

```text
protect normal branches near collision boundary without globally shrinking all
residual components.
```

### 2. Active-Source Steering Guard

For the known active source:

```text
seed: 77025
source_index: 12
step: 24
```

Require a low normal steering gate:

```text
L_active_steer =
  relu(g_steer_n - g_steer_active_max)^2
```

Initial:

```text
g_steer_active_max: 0.50
```

This is stricter than generic low-margin suppression because M792 showed that
steer residual specifically causes the alpha `0.2` active-source collision.

### 3. Intervention Steering Retention

For intervention rows, especially hard-negative or outcome-sensitive rows:

```text
L_intervention_steer_retention =
  w_intervention * relu(g_steer_floor - g_steer_i)^2
```

Initial:

```text
g_steer_floor: 0.75
```

Use stronger weights when M792/M773 evidence marks the row as intervention
sensitive:

```text
hard_negative_available
large normal/intervention action gap
large margin gap from normal
source-diverse positive row
```

### 4. Brake Retention

Brake was useful-only in M792, so it should default high and receive no active
normal suppression unless a later audit finds brake-specific harm:

```text
L_brake_retention =
  relu(g_brake_floor - g_brake)^2
```

Initial:

```text
g_brake_floor: 0.75
```

### 5. Steer Contrast

For matched normal/intervention pairs, when the normal row is low-margin:

```text
L_steer_contrast =
  softplus(g_steer_n - g_steer_i + margin)
```

Initial:

```text
margin: 0.20
```

Purpose:

```text
teach the calibrator the relation M792 exposed: suppress normal steering
residual at the boundary while retaining intervention steering residual.
```

### 6. Trust Region

Keep the calibrator close to the high-default initialization unless evidence
requires a change:

```text
L_trust =
  ||g_steer - 0.85||^2 + ||g_brake - 0.85||^2
```

Use a lower trust weight on low-margin normal steering rows and a higher trust
weight on high-margin normal and intervention rows.

## Metrics

M795 should write:

```text
summary.json
alpha_metrics.csv
objective_rows.csv
replay_rows.csv
gate_metrics.csv
component_gate_metrics.csv
active_source_metrics.csv
rejected_rows.csv
```

Required gate metrics:

```text
gate_steer_normal_mean
gate_steer_low_margin_normal_mean
gate_steer_intervention_mean
gate_brake_normal_mean
gate_brake_intervention_mean
gate_throttle_mode
steer_contrast_mean
active_source_steer_gate_mean
component_selectivity_pass
```

## Candidate Rules

Primary alpha:

```text
0.2
```

Alpha ladder:

```text
0.0, 0.125, 0.15, 0.2
```

Strong candidate:

```text
strict normal retention passes
active-source margin >= M786 alpha 0.15 active margin
intervention gap mean >= M780 alpha 0.125 gap mean
component_selectivity_pass is true
```

Limited candidate:

```text
strict normal retention passes
active-source margin >= M786 alpha 0.15 active margin
intervention gap mean > M786 alpha 0.15 gap mean
component_selectivity_pass is true
```

Reference thresholds:

```text
M786 alpha 0.15 gap mean: 0.043397390743
M786 alpha 0.15 active margin: 0.000028245983
M780 alpha 0.125 gap mean: 0.044046541597
```

Component selectivity pass should require:

```text
active-source g_steer_normal_mean <= 0.55
g_steer_intervention_mean >= 0.70
g_brake_intervention_mean >= 0.70
g_steer_intervention_mean - g_steer_low_margin_normal_mean >= 0.15
```

These are diagnostic thresholds. They do not promote a checkpoint.

## Failure Classification

M795 should classify outcomes as:

```text
v4_steer_attributed_calibration_strong_candidate
v4_steer_attributed_calibration_limited_candidate
v4_steer_attributed_calibration_no_gap_lift
v4_steer_attributed_calibration_normal_retention_failed
v4_steer_attributed_calibration_component_collapse
v4_steer_attributed_calibration_metadata_artifact
```

`component_collapse` should fire if the learned gates behave like another
scalar gate, for example:

```text
abs(g_steer_mean - g_brake_mean) < 0.02
and g_steer_intervention_mean - g_steer_low_margin_normal_mean < 0.05
```

## Stop Conditions

M795 should stop and audit before further objective tuning if:

```text
1. no alpha passes strict normal retention;
2. strict normal retention passes only by killing intervention gap;
3. steering gate collapses to scalar behavior;
4. throttle unexpectedly becomes necessary without fresh evidence;
5. training metrics improve but closed-loop replay does not.
```

## Decision

M794 admits only:

```text
m795-v4-steer-attributed-residual-calibration-implementation
```

M795 may implement and run the no-PPO steer-attributed calibration diagnostic.
It must not mutate the base actor or M761 residual head, run PPO, or promote a
checkpoint.
