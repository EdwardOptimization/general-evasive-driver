# M788 V4 Vector Residual Calibration Design

## Purpose

M788 designs the next no-PPO calibration probe after M787 audited M786 as a
limited scalar-gate positive.

The question is:

```text
Can action-component-aware residual calibration protect low-margin normal
branches without globally shrinking useful intervention residuals?
```

This milestone is design-only:

```text
no implementation
no replay run
no actor update
no residual-head update
no optimizer run
no PPO
no checkpoint promotion
```

## Motivation

M786 proved that scalar gating can cross the registered threshold:

```text
M786 alpha 0.15:
  normal_success/collision: 1.000000 / 0.000000
  intervention_gap_mean: 0.043397
  margin_gap_mean: 0.031901
  active_source_min_margin: +0.000028
```

But M787 found the result too close to alpha scaling:

```text
M780 alpha 0.125 intervention_gap_mean: 0.044047
M786 alpha 0.15  intervention_gap_mean: 0.043397

M783 final gate means: 0.499727 / 0.499986
M786 final gate means: 0.670088 / 0.683384
intended high-default gate: about 0.85
```

The scalar gate has a structural limitation:

```text
delta_calibrated = g(feature) * delta_raw
```

It cannot suppress a risky steering component while keeping a useful braking or
throttle component. The next probe should keep the same frozen base actor and
frozen M761 residual head, but allow per-action residual scaling.

## Actor Contract

The deployable actor contract does not change:

```text
P0 human-view no-wheel 72-dim frame + online GRU hidden state
```

Allowed deploy-time calibrator input:

```text
same deployable actor feature used by the frozen M761 residual head
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
```

Training-time terminal margins, source labels, intervention variants, and fault
metadata may only weight losses and produce audit tables.

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

M789 should add the smallest more expressive calibrator:

```text
ResidualVectorGate(feature) -> g in [0, 1]^3
```

Executed residual action:

```text
delta_raw = residual_head(feature)
delta_calibrated = g(feature) * delta_raw
action = base_action + alpha * delta_calibrated
```

where `*` is elementwise over:

```text
steer
throttle
brake
```

Initial gate:

```text
g0 = [0.85, 0.85, 0.85]
```

The first implementation should not add an unrestricted additive residual. A
per-dimension gate is enough to test the M787 hypothesis while preserving the
M761 residual direction as the reference.

## Data

Use the same current evidence corpus:

```text
runs/m773_v4_broader_source_holdout_corpus_export/positive_sequence_outcomes.csv
runs/m773_v4_broader_source_holdout_corpus_export/contrast_rows.csv
configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json
runs/m780_v4_broader_normal_boundary_alpha_probe/replay_rows.csv
```

The active source must remain visible:

```text
seed: 77025
source_index: 12
step: 24
fault_family_pair: drive_authority_drop->rear_lateral_authority_drop
```

M789 should reconstruct tensors by replay, not by trusting CSV action values as
complete training tensors.

## Objective Terms

M789 should train only the vector calibrator parameters.

### 1. Low-Margin Normal Component Suppression

For normal-history rows:

```text
L_low_margin_normal =
  low_margin_weight * ||g_n * delta_n||^2
```

Use the M786 low-margin weight:

```text
low_margin_weight =
  clip((m_cutoff - normal_margin_base) / m_cutoff, 0, 1)^2

m_cutoff: 0.001
```

This pressure should be strong only on low-margin normal rows. High-margin
normal rows should keep high gates.

### 2. High-Default Non-Low-Margin Prior

For non-low-margin normal rows:

```text
L_high_default_normal =
  (1 - low_margin_weight) * ||relu(g_default - g_n)||^2
```

For intervention rows:

```text
L_high_default_intervention =
  active_component_mask * ||relu(g_default - g_i)||^2
```

Initial:

```text
g_default: 0.85
```

The `active_component_mask` should only apply to components where the raw
residual is meaningful:

```text
abs(delta_component) >= max(0.002, 0.25 * max_abs_delta_for_row)
```

This avoids forcing high gates on components whose residual is effectively
zero.

### 3. Active Boundary Normal Guard

For the active source:

```text
L_active_normal =
  ||relu(g_n - g_active_max)||^2
```

Initial:

```text
g_active_max: 0.55
```

If this term alone forces all three components low, M789 should report that as
continued scalar-like behavior rather than hiding it.

### 4. Intervention Component Retention

For outcome-critical intervention rows:

```text
L_intervention_floor =
  active_component_mask * ||relu(g_intervention_min - g_i)||^2
```

Initial:

```text
g_intervention_min: 0.80
```

Purpose:

```text
keep useful intervention residual components active even when the paired normal
branch receives low-margin suppression.
```

### 5. Component-Selective Gate Contrast

For low-margin normal/intervention pairs:

```text
L_component_contrast =
  low_margin_weight * active_component_mask
  * ||relu(g_margin - (g_i - g_n))||^2
```

Initial:

```text
g_margin: 0.20
```

This is the direct test of whether vector gates can create component-level
normal/intervention separation that the scalar gate could not.

### 6. Closed-Loop Gap Proxy

Keep the original action-gap threshold:

```text
target_gap = base_gap + 0.003
```

Do not weaken this after seeing M783/M786 near misses.

### 7. Hard-Negative Term

Retain the optional hard-negative term from M783/M786:

```text
L_hard_negative =
  relu(hard_gap_target - hard_gap)^2
```

If hard-negative rows are unavailable, skip the term and report the available
fraction.

## Alpha Ladder

M789 should evaluate:

```text
alpha: 0.0, 0.125, 0.15, 0.2
```

Primary target:

```text
alpha 0.2
```

Reason:

```text
M786 already found a narrow alpha 0.15 candidate. The value of vector
calibration is whether it can make the stronger alpha 0.2 residual useful
without normal collision.
```

## Pass Criteria

Required implementation gates:

```text
sample_reconstruction_success_rate >= 0.98
metadata_missing_rows == 0
actor_backbone_changed == false
base_residual_head_changed == false
optimizer_updates_only_vector_calibrator == true
ppo_used == false
promoted == false
```

Strict normal retention:

```text
normal_success_rate == 1.0
normal_collision_rate == 0.0
```

Original gap gate:

```text
intervention_action_gap_mean >= base_gap_mean + 0.003
intervention_action_gap_p10 >= base_gap_p10
outcome_sensitivity_retention_rate == 1.0
```

Baseline references:

```text
base_gap_mean: 0.040348
base_gap_p10: 0.025782
M780 alpha 0.125 gap mean: 0.044047
M786 alpha 0.15 gap mean: 0.043397
M786 alpha 0.15 active margin: +0.000028
```

Strong vector candidate:

```text
alpha 0.2 passes strict normal retention
alpha 0.2 active_source_min_margin >= +0.000028
alpha 0.2 intervention_gap_mean >= 0.044047
```

Limited vector candidate:

```text
some alpha passes strict normal retention and original gap gate
and Pareto-improves M786 alpha 0.15 on:
  active_source_min_margin
  intervention_gap_mean
```

Do not mark a candidate if it merely reproduces M786 alpha `0.15` with another
gate.

## Required Metrics

M789 should write:

```text
summary.json
alpha_metrics.csv
training_metrics.csv
objective_rows.csv
replay_rows.csv
rejected_rows.csv
```

Additional vector-gate metrics:

```text
gate_normal_mean_steer/throttle/brake
gate_intervention_mean_steer/throttle/brake
gate_active_source_normal_mean_steer/throttle/brake
gate_active_source_intervention_mean_steer/throttle/brake
component_contrast_mean_steer/throttle/brake
component_gate_std_steer/throttle/brake
component_collapse_flags
```

The audit must show whether vector calibration used component selectivity or
simply learned another global scaling value.

## Result Classes

M789 should classify:

```text
v4_vector_residual_calibration_strong_candidate:
  alpha 0.2 satisfies the strong vector candidate criteria

v4_vector_residual_calibration_limited_candidate:
  a lower alpha Pareto-improves M786 alpha 0.15 while passing gates

v4_vector_residual_calibration_no_pareto_lift:
  normal retention passes but no alpha improves the M786 Pareto point

v4_vector_residual_calibration_normal_regression:
  gap improves but strict normal retention fails

v4_vector_residual_calibration_component_collapse:
  vector gates behave like global scalar scaling

v4_vector_residual_calibration_reconstruction_blocked:
  reconstruction or metadata gates fail

v4_vector_residual_calibration_metadata_artifact:
  actor/residual mutation PPO or promotion occurs
```

## Implementation Guardrails

M789 must:

```text
freeze base actor parameters;
freeze M761 residual head parameters;
train only the vector calibrator;
record actor and residual checksums before and after;
record vector calibrator checksum and parameter count;
keep hard-negative sparsity visible;
write component-level gate metrics;
compare against M780 M783 and M786;
avoid PPO;
avoid checkpoint promotion.
```

M789 must not:

```text
train the base actor;
train or overwrite M761 residual head;
use fault labels as deploy-time inputs;
hide alpha 0.2 active-source failure if it persists;
call a lower-alpha diagnostic result a promoted driver;
claim true four-wheel/single-wheel physical-failure coverage.
```

## Decision

M788 admits one implementation milestone:

```text
m789-v4-vector-residual-calibration-implementation
```

If M789 cannot beat the M786 alpha `0.15` Pareto point, the branch should audit
that as evidence that residual calibration is becoming local gate-passing and
should either stop or pivot back to corpus/architecture evidence.
