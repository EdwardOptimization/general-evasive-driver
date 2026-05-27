# M1055 V4 Public Base Post Short-Promotion Surface Refresh

## Purpose

M1055 runs the current-base source-diverse wrong-history boundary surface
refresh designed in M1054.

This milestone does not train, run PPO, use private holdout, change actor
inputs, or promote a checkpoint.

## Family

```text
short61049:
  runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt

short61050:
  runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt

short61051:
  runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt
```

## Stage 1: Matched-Current Mining

Artifact:

```text
runs/m1055_post_short_promotion_matched_current_seed105400
```

Result:

```text
candidate_pair_count: 312405
accepted_pair_count: 926
accepted_physical_pair_count: 97
accepted_left_step_count: 25
accepted_source_obstacle_bucket_count: 18
ambiguity_surface_found: true
```

Target coverage:

```text
future_braking_deceleration: 671
future_yaw_response: 255
```

The promoted short-PPO family still has a substantial matched-current
ambiguity pool under the zero-obstacle-relvel profile.

## Stage 2: Outcome Gate

Artifact:

```text
runs/m1055_post_short_promotion_outcome_seed105400
```

Result:

```text
input_pair_count: 926
outcome_row_count: 5556
outcome_summary_rows: 54
```

The matched-current ambiguity pool produced outcome interventions for boundary
relocation.

## Stage 3: Boundary Relocation

Artifact:

```text
runs/m1055_post_short_promotion_boundary_surface_seed105400
```

Result:

```text
candidate_count: 926
row_count: 18375
accepted_wrong_history_rows: 315
accepted_wrong_history_pairs: 47
accepted_reset_rows: 1387
accepted_zero_current_rows: 1180
wrong_history_success_drop_count: 315
surface_found: true
```

This is a strong outcome-sensitivity signal. The refresh did not fail because
wrong-history sensitivity disappeared.

## Stage 4: Robustness Gate

Artifact:

```text
runs/m1055_post_short_promotion_boundary_robustness_seed105400
```

Result:

```text
decision: reject_boundary_bucket_tuned_surface
passed: false
accepted_wrong_rows: 315
accepted_wrong_physical_pairs: 15
accepted_wrong_left_steps: 7
accepted_wrong_checkpoints: 3
accepted_wrong_targets: 3
accepted_wrong_normal_margin_buckets: 1
accepted_wrong_success_drop_fraction: 1.0
max_rows_per_physical_pair_fraction: 0.190476
control_accepted_wrong_rows: 0
```

All robustness gates passed except normal-margin bucket diversity:

```text
accepted_wrong_rows: pass, 315 >= 80
physical_pairs: pass, 15 >= 10
left_steps: pass, 7 >= 5
checkpoints: pass, 3 >= 3
targets: pass, 3 >= 2
normal_margin_buckets: fail, 1 < 2
success_drop_fraction: pass, 1.0 >= 1.0
max_rows_per_pair_fraction: pass, 0.190476 <= 0.25
control_accepted_wrong_rows: pass, 0 <= 0
```

Accepted wrong-history margin range:

```text
normal_margin_min: 0.0004777225
normal_margin_mean: 0.0030149520
normal_margin_max: 0.0099828307
margin_gap_mean: 0.0055409903
margin_gap_max: 0.0102249832
```

The surface is rich and source-diverse, but all accepted normal margins fall
inside the `0.00-0.01 m` bucket under the pre-registered `0.01` bucket width.

## Classification

```text
result_class: post_short_promotion_surface_refresh_margin_bucket_sparse
failure_types: scenario_sampling_failure
```

This is not:

```text
wrong-history-insensitive
duplicate-dominated
training artifact
contract violation
```

It is a margin-bucket diversity failure on an otherwise strong current-base
wrong-history boundary surface.

## Decision

Do not convert this surface directly into a protected corpus yet.

Next step should audit whether this is a coarse bucket-edge artifact or a real
source sampling limitation:

```text
m1056-v4-public-base-post-short-promotion-margin-bucket-audit
```

M1056 should use the already produced M1055 rows, not new PPO or training, and
diagnose:

```text
1. whether narrower pre-registered diagnostic bucket widths reveal real margin
   diversity inside the 0.00-0.01 m range;
2. whether the accepted margin distribution is too concentrated near a single
   obstacle/window setting;
3. whether the correct next route is compact corpus conversion with a revised
   bucket rule or a retargeted mining wave for wider margin coverage.
```

## Decision

```text
post_short_promotion_surface_refresh_margin_bucket_sparse_route_to_bucket_audit
```

Next:

```text
m1056-v4-public-base-post-short-promotion-margin-bucket-audit
```
