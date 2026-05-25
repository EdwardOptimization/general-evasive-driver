# M929 V4 Public-Base Policy-Level Trust-Region Design

## Purpose

M929 opens the `v4_public_base_policy_level_trust_region` branch after M927
showed that the residual-head bridge is infeasible under the registered gates.

M929 is design-only:

```text
no training
no replay
no PPO
no checkpoint promotion
```

## Why Policy-Level Now

The residual bridge failed for a specific reason:

```text
M921 residual: target-aligned and normal-retaining, but weak low-tail lift.
M924 residual: strong low-tail lift, but non-retaining and target-conflicting.
M927 mixtures: no alpha/mix row satisfies all gates.
```

This does not prove the public M399 actor cannot be improved. It proves the
current frozen-feature residual-head bridge is not the right control surface.

The next controlled route is therefore not PPO. It is a small policy-level
trust-region objective sanity probe.

## Design Goal

M930 should answer:

```text
Can a tightly constrained actor policy-head update move M399 in a way the
residual bridge could not, while preserving objective-level proof gates?
```

M930 remains objective sanity only. It must not run replay or PPO.

## Actor Contract

Actor inputs remain unchanged:

```text
P0 human-view no-wheel 72-dim frame + online GRU hidden state
```

M930 must not add:

```text
mu
mass / tire / brake / actuator hidden parameters
slip or tire forces
feasibility labels
TTC / required clearance / stopping distance
path reference fields
controller mode
```

## Update Scope

M930 should update only the final policy mean head:

```text
model.actor_mean
```

Freeze:

```text
response encoder
context encoder
GRU / recurrent state mechanics
critic
log_std
all observation contracts
```

Rationale:

```text
1. This is more expressive than a separate residual head because it directly
   changes the policy output surface.
2. It is still less risky than a full actor update because feature extraction
   and recurrent state encoding remain fixed.
3. It produces an actual actor checkpoint, unlike residual-only diagnostics.
```

## Objective Inputs

M930 should use:

```text
base checkpoint:
  runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt

source corpus:
  runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv
  runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv

target rows:
  runs/m919_v4_public_base_expanded_target_regeneration/accepted_target_rows.csv

low-tail metrics:
  runs/m912_v4_public_base_sequence_recalibration_audit/summary.json
  runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv

negative feasibility evidence:
  runs/m927_v4_public_base_residual_direction_feasibility/summary.json
```

## Objective

Use cached M399 features from the same reconstruction path used by M921-M927.
For an updated `actor_mean`, compute:

```text
new_normal_action = tanh(actor_mean(normal_features))
new_intervention_action = tanh(actor_mean(intervention_features))
gap = ||new_intervention_action - new_normal_action||
deficit = relu(target_gap - gap)
```

Loss groups:

```text
target_action_loss:
  M919 target-action MSE on accepted target rows.

low_tail_gap_loss:
  low-tail floor and deficit losses on M912 low-tail rows.

normal_retention_loss:
  keep new_normal_action close to M399 base normal_action over all 1213 rows.

intervention_anchor_loss:
  keep new_intervention_action bounded to avoid artificial gap from unstable
  wrong-history branch movement.

parameter_anchor_loss:
  L2 anchor from updated actor_mean parameters to base actor_mean parameters.
```

Suggested initial weights:

```text
target_action_coef: 0.5
low_tail_gap_floor_coef: 2.0
low_tail_deficit_coef: 1.0
normal_retention_coef: 8.0
intervention_anchor_coef: 1.0
parameter_anchor_coef: 0.01
```

These are starting points for an objective sanity probe, not promotion claims.

## Interpolation

M930 should save candidate checkpoints by interpolating actor parameters between
base and raw updated policy head:

```text
alpha:
  0.001, 0.002, 0.005, 0.010, 0.020, 0.050, 0.100
```

Only the updated `actor_mean` parameters should be interpolated. All other
parameters remain exactly M399.

## Candidate Gate

M930 may admit an objective candidate only if:

```text
sample_reconstruction_success_rate >= 0.98
actor_input_contract_unchanged == true
feature_backbone_changed == false
critic_changed == false
log_std_changed == false
candidate_alpha_count >= 1
```

For an alpha to count as candidate:

```text
normal_anchor_mse_mean <= 0.000004
normal_anchor_mse_p95 <= 0.000025
first_action_drift_from_base_mean <= 0.003
first_action_drift_from_base_p95 <= 0.008
normal_intervention_gap_p10 >= M912 near_base_gap_p10 + 0.004
gap_deficit_mean <= M912 near_base_gap_deficit_mean - 0.002
low_tail_fraction <= M912 low_tail_fraction - 0.05
target_action_mse_mean improves versus alpha 0.0
strict_target_action_mse_mean improves versus alpha 0.0
```

## Outputs

M930 should write:

```text
runs/m930_v4_public_base_policy_head_trust_region_probe/summary.json
runs/m930_v4_public_base_policy_head_trust_region_probe/training_metrics.csv
runs/m930_v4_public_base_policy_head_trust_region_probe/alpha_metrics.csv
runs/m930_v4_public_base_policy_head_trust_region_probe/objective_rows.csv
runs/m930_v4_public_base_policy_head_trust_region_probe/checkpoints/
runs/m930_v4_public_base_policy_head_trust_region_probe/rejected_rows.csv
```

The summary must include checksums for:

```text
full model before/after
actor_mean before/after
feature backbone before/after
critic before/after
log_std before/after
```

## Route Decision

If M930 finds an objective candidate:

```text
route to exact no-update compatibility design for the selected alpha
```

If M930 changes only actor_mean but still has no candidate:

```text
route to policy-level trust-region audit before any broader actor update
```

If M930 changes frozen components:

```text
classify as contract artifact and reject
```

## Safeguards

M930 must not:

```text
change actor inputs;
update feature/recurrent encoders;
run replay;
run PPO;
promote a checkpoint;
claim driver improvement from objective-only metrics.
```

## Decision

Decision:

```text
public_base_policy_level_trust_region_design_admit_m930
```

Next:

```text
m930-v4-public-base-policy-head-trust-region-probe-implementation
```
