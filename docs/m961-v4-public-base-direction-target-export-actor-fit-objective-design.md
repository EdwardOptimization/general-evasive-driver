# M961 V4 Public Base Direction Target Export Actor-Fit Objective Design

## Purpose

M961 designs the route after M960 found joint direction-target candidates.

It does not train, update model weights, run PPO, change actor inputs, use
private holdout, or promote.

M960 changed the branch state:

```text
result_class: low_tail_direction_family_target_audit_joint_candidate
joint_direction_target_candidate_count: 20
primary_joint_candidate_count: 20
best_joint_candidate_family: throttle_minus_amp_0_0080
```

The next step is not to train immediately. The accepted target candidates must
first be exported into a branch-separated corpus that keeps low-tail normal
targets, wrong-history proof anchors, and ordinary behavior-retention anchors
distinct.

## Accepted Target Source

M962 should accept only rows where:

```text
family_type == primary
normal_retention_pass == true
behavior_grounded == true
m267_target_preflight_pass == true
joint_direction_target_candidate == true
```

From M960 this yields 20 target families:

```text
brake_plus_amp_0_0010
brake_plus_amp_0_0020
brake_plus_amp_0_0040
brake_plus_amp_0_0060
brake_plus_amp_0_0080

steer_minus_brake_plus_amp_0_0010
steer_minus_brake_plus_amp_0_0020
steer_minus_brake_plus_amp_0_0040
steer_minus_brake_plus_amp_0_0060
steer_minus_brake_plus_amp_0_0080

throttle_minus_amp_0_0010
throttle_minus_amp_0_0020
throttle_minus_amp_0_0040
throttle_minus_amp_0_0060
throttle_minus_amp_0_0080

toward_intervention_amp_0_0010
toward_intervention_amp_0_0020
toward_intervention_amp_0_0040
toward_intervention_amp_0_0060
toward_intervention_amp_0_0080
```

M962 must not export diagnostic-only families:

```text
away_from_intervention
throttle_plus
brake_minus
steer_plus
```

Secondary families can be carried as diagnostics but not as training targets:

```text
steer_minus
steer_plus_brake_plus
```

## Export Artifacts

M962 should write:

```text
runs/m962_v4_public_base_direction_target_export/summary.json
runs/m962_v4_public_base_direction_target_export/accepted_direction_targets.csv
runs/m962_v4_public_base_direction_target_export/direction_target_family_catalog.csv
runs/m962_v4_public_base_direction_target_export/branch_separated_proof_targets.csv
runs/m962_v4_public_base_direction_target_export/retention_anchor_targets.csv
runs/m962_v4_public_base_direction_target_export/rejected_export_candidates.csv
runs/m962_v4_public_base_direction_target_export/route_decision.csv
```

### accepted_direction_targets.csv

One row per accepted target-family and low-tail row:

```text
target_id
target_family
direction_family
amplitude
family_rank
seed
step
contrast_group_id
source_index
base_steer
base_throttle
base_brake
target_steer
target_throttle
target_brake
delta_steer
delta_throttle
delta_brake
terminal_margin_delta
terminal_margin_p10_delta_family
positive_margin_fraction_family
normal_anchor_mse_mean_family
first_action_drift_mean_family
m267_target_preflight_pass
target_weight
```

The target action is:

```text
target_action = clamp(base_normal_action + amplitude * unit_direction)
```

The direction definitions are the same as M959/M960.

### direction_target_family_catalog.csv

One row per accepted family, preserving M960 audit fields:

```text
target_family
direction_family
amplitude
terminal_margin_mean_delta
terminal_margin_p10_delta
positive_margin_fraction
normal_retention_pass
normal_anchor_mse_mean
first_action_drift_from_base_mean
m267_target_preflight_pass
recommended_weight
export_role
```

Recommended initial weights:

```text
throttle_minus: 1.00
toward_intervention: 0.80
brake_plus: 0.80
steer_minus_brake_plus: 0.70
```

These weights are not controller rules. They are supervised loss weights for
the target-fitting stage and should remain visible in the exported corpus.

### branch_separated_proof_targets.csv

This file protects the M267/M264 self-ID proof relation:

```text
same relocated current scene;
normal hidden should stay on normal-success target;
wrong hidden should stay on wrong-history failure-preserving target.
```

Fields:

```text
proof_row_id
target_family
branch
left_seed
right_seed
left_step
right_step
base_action
target_action
target_role
expected_success
expected_wrong_history_success
success_drop_required
```

Rules:

- normal branch target should be near the base normal action unless a known
  normal-success override is explicitly available;
- wrong-history branch target must be the base wrong-history action or a
  wrong-failure-preserving target;
- wrong-history targets must not be replaced by normal safe targets.

### retention_anchor_targets.csv

This file anchors ordinary behavior outside accepted low-tail target rows.

Fields:

```text
seed
step
variant
base_action
anchor_weight
anchor_role
```

At minimum it should include:

```text
non-target positive rows sampled from M755
accepted-target rows not selected by M960
M267/M264 active-row base actions
```

## Actor-Fit Objective Design

The first actor-fit stage should be a constrained objective-only probe, not PPO.

Trainable surface:

```text
preferred first pass: actor_mean only
fallback if no fit: actor_mean + response_context_fusion.0
forbidden initially: response encoder, context encoder, GRU, critic, log_std
```

Objective:

```text
L =
  w_direction * MSE(actor_mean(o, h_normal), accepted_direction_target)
+ w_proof_normal * MSE(actor_mean(o_relocated, h_normal), normal_proof_target)
+ w_proof_wrong * MSE(actor_mean(o_relocated, h_wrong), wrong_failure_target)
+ w_retention * MSE(actor_mean(o_anchor, h_anchor), base_action)
+ w_kl * action_mean_drift_to_base
```

Initial coefficient intent:

```text
w_direction: 1.0
w_proof_normal: 1.0
w_proof_wrong: 2.0
w_retention: 0.5
w_kl: 0.1
```

These coefficients are design defaults for the next implementation. M962 should
only export the target corpus; actor fitting should remain a later milestone
after export validation.

## Exact Gates Before Any Promotion

The actor-fit implementation after M962 must pass gates in this order:

```text
1. target export sanity:
   accepted families only, no diagnostic-only target export

2. exact target-fit metrics:
   accepted_direction_target_mse improves
   proof_wrong_anchor_mse does not regress
   retention_anchor_mse stays inside tolerance

3. M267/M264 active proof preflight:
   rows 6, 13, 15, 16 pass
   success_drop_count remains 17 / 17 in full preflight

4. public replay stack:
   M183/M168
   M183/M170
   M193/M189
   M212/M204
   M223/M219
   M267/M264

5. behavior seeds:
   9505
   9506
```

No private holdout should be used for this branch. Promotion remains blocked.

## Route Logic

If M962 exports a valid target corpus:

```text
route: direction-target actor-fit objective implementation
```

If export filtering removes all accepted candidates:

```text
route: M960 target audit bug fix or source-diverse target refresh
```

If branch-separated proof targets cannot be exported:

```text
route: branch-separated direction target refinement
```

If the accepted corpus is dominated by one family or one row source:

```text
route: source-diverse direction target refresh
```

## Decision For Next Milestone

M961 routes to:

```text
m962-v4-public-base-direction-target-export-implementation
```

M962 should implement the no-training export. It must not train, run PPO,
change actor inputs, use private holdout, or promote.
