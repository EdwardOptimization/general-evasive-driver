# M1161 V4 Public Base Row15 Promoted Margin-Slack Surface Refresh Run

## Purpose

M1161 runs the three-stage margin-slack surface refresh designed in M1160 for
the M1158 `alpha_0_05` public-gate base.

It does not train actor weights, run PPO, promote, use private holdout, change
actor inputs, weaken thresholds, or convert the surface into an objective
corpus.

## Commands

M1161 ran:

```text
1. matched_current_response_ambiguity
2. matched_history_outcome_gate
3. source_balanced_boundary_relocation_surface
```

All commands used the six-policy family from M1160:

```text
row15_current:
  runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
row15_previous_alpha015:
  runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
previous_m1078_base:
  runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
short61049:
  runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt
short61050:
  runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt
short61051:
  runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt
```

## Stage 1: Matched-Current Mining

The matched-current ambiguity stage succeeded:

```text
candidate_pair_count: 564840
accepted_pair_count: 4585
accepted_physical_pair_count: 242
accepted_left_step_count: 27
accepted_source_obstacle_bucket_count: 24
accepted_by_target:
  future_braking_deceleration: 1600
  future_lateral_accel_response: 1600
  future_yaw_response: 1385
ambiguity_surface_found: true
```

This means source coverage was not the initial blocker.

## Stage 2: Outcome Gate

The matched-history outcome gate completed:

```text
input_pair_count: 4585
outcome_row_count: 27510
outcome_summary_rows: 108
```

## Stage 3: Source-Balanced Relocation

The relocation source budget was ready:

```text
candidate_wrong_history_rows: 4585
eligible_physical_pairs: 242
eligible_left_steps: 27
eligible_checkpoints: 6
eligible_targets: 3
source_budget_ready: true
```

The candidate selection stage also stayed diverse:

```text
selected_rows: 1200
selected_physical_pairs: 242
selected_left_steps: 27
selected_targets: 3
max_selected_rows_per_physical_pair: 5
max_selected_pair_fraction: 0.004167
decision: source_balanced_candidates_ready
```

The failure happened after boundary relocation:

```text
decision: reject_duplicate_dominated_boundary_surface
passed: false
raw_rows: 21250
accepted_wrong_rows: 15
accepted_wrong_physical_pairs: 2
accepted_wrong_left_steps: 2
accepted_wrong_checkpoints: 2
accepted_wrong_targets: 1
accepted_wrong_normal_margin_buckets: 1
accepted_wrong_success_drop_fraction: 1.0
accepted_wrong_normal_margin_max: 0.002483
max_rows_per_physical_pair_fraction: 0.666667
control_accepted_wrong_rows: 0
```

Against the M1160 pre-registered slack gate:

```text
accepted_wrong_history_rows: 15 < 100
accepted_wrong_physical_pairs: 2 < 12
accepted_wrong_left_steps: 2 < 6
accepted_wrong_checkpoints: 2 < 4
accepted_wrong_targets: 1 < 2
accepted_wrong_normal_margin_buckets: 1 < 3
accepted_wrong_normal_margin_max: 0.002483 < 0.01
max_rows_per_physical_pair_fraction: 0.666667 > 0.25
```

Rows that did pass were true success drops and control rows stayed rejected,
but the accepted wrong-history surface is too small, too duplicate-dominated,
and too low-slack to convert.

## Result Class

```text
result_class: row15_promoted_margin_slack_surface_refresh_duplicate_dominated
failure_types:
  - scenario_sampling_failure
  - objective_overfit
```

This is not a training failure, PPO failure, contract violation, or private
holdout issue. It is a surface-quality failure: the broad candidate set exists,
but the relocation step cannot currently produce a source-diverse,
margin-slack wrong-history surface.

## Interpretation

M1161 falsifies the immediate assumption that the new `alpha_0_05` public base
has a fresh, source-diverse wrong-history surface with nontrivial margin slack
under the M1160 pipeline.

The result does not invalidate the M1158 promotion. M1158 was a public
proof-base hardening promotion based on existing public gates. M1161 only says
that the next fresh current-base surface is not ready for objective conversion
or PPO support.

## Artifacts

```text
runs/m1161_row15_promoted_margin_slack_matched_current_seed116100/summary.json
runs/m1161_row15_promoted_margin_slack_matched_current_seed116100/matched_pairs.csv
runs/m1161_row15_promoted_margin_slack_outcome_seed116100/summary.json
runs/m1161_row15_promoted_margin_slack_outcome_seed116100/outcome_interventions.csv
runs/m1161_row15_promoted_margin_slack_surface_seed116100/summary.json
runs/m1161_row15_promoted_margin_slack_surface_seed116100/robustness_gates.csv
runs/m1161_row15_promoted_margin_slack_surface_seed116100/surface_summary.csv
runs/m1161_row15_promoted_margin_slack_surface_seed116100/balanced_accepted_wrong_history_rows.csv
```

## Decision

Do not weaken thresholds inside M1161 and do not convert the failed surface.
Route to a failure audit that separates source-budget, outcome-gate,
relocation-target, wrong-history-sensitivity, and margin-slack causes.

```text
decision: row15_promoted_margin_slack_surface_refresh_reject_route_to_failure_audit
next: m1162-v4-public-base-row15-promoted-margin-slack-surface-refresh-failure-audit
```
