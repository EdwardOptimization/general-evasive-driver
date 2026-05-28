# M1160 V4 Public Base Row15 Promoted Margin-Slack Surface Refresh Design

## Purpose

M1160 designs a fresh source-diverse protected/preference surface refresh for
the M1158 `alpha_0_05` public-gate base.

This milestone is design-only. It does not mine rows, run replay, train actor
weights, run PPO, promote, use private holdout, or change actor inputs.

## Current Base

```text
runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
```

Treat this as the primary current policy.

## Refresh Family

Use the new public base plus nearby public-family checkpoints:

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

Only `row15_current` is the current public-gate base. The other policies are
source-diversity anchors and should not be treated as promoted bases.

## Why Refresh

M1158 promoted `alpha_0_05` as public proof-base hardening, but the selected
projection still has a near-boundary wrong-history margin:

```text
row15_promoted_materialized wrong_history_margin_max: -0.000000497
```

The next PPO proposal should not depend only on this thin repair surface. The
project needs a new current-base surface that is source-diverse and has explicit
margin-slack coverage.

M1161 should therefore use the existing source-balanced boundary tooling, but
with acceptance criteria that make slack visible:

```text
normal margin bucket coverage at 0.005 m
normal margin max
source/checkpoint diversity
physical-pair diversity
success-drop fraction
control-row rejection
```

## M1161 Pipeline

M1161 should run three stages.

### 1. Matched-Current Ambiguity Mining

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.matched_current_response_ambiguity \
  --checkpoint-policy row15_current=runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt \
  --checkpoint-policy row15_previous_alpha015=runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt \
  --checkpoint-policy previous_m1078_base=runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt \
  --checkpoint-policy short61049=runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt \
  --checkpoint-policy short61050=runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt \
  --checkpoint-policy short61051=runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --probe-seeds 116100,116101,116102,116103 \
  --episodes 40 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 1800 \
  --nearest-k 12 \
  --max-visible-quantile 0.05 \
  --min-target-z-delta 1.0 \
  --max-pairs-per-target 420 \
  --max-pairs-per-physical-pair 1 \
  --max-pairs-per-left-step 20 \
  --max-pairs-per-source-obstacle-bucket 40 \
  --obstacle-distance-bucket-width 5.0 \
  --obstacle-lateral-bucket-width 1.0 \
  --min-accepted-pairs 100 \
  --device cpu \
  --run-dir runs/m1161_row15_promoted_margin_slack_matched_current_seed116100
```

### 2. Matched-History Outcome Gate

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.matched_history_outcome_gate \
  --checkpoint-policy row15_current=runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt \
  --checkpoint-policy row15_previous_alpha015=runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt \
  --checkpoint-policy previous_m1078_base=runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt \
  --checkpoint-policy short61049=runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt \
  --checkpoint-policy short61050=runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt \
  --checkpoint-policy short61051=runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --pairs-csv runs/m1161_row15_promoted_margin_slack_matched_current_seed116100/matched_pairs.csv \
  --delay-steps 10 \
  --max-continuation-steps 60 \
  --min-margin-gap 0.02 \
  --max-pairs-per-checkpoint-target 0 \
  --pair-label-mode matching \
  --device cpu \
  --run-dir runs/m1161_row15_promoted_margin_slack_outcome_seed116100
```

### 3. Source-Balanced Boundary Relocation

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.source_balanced_boundary_relocation_surface \
  --checkpoint-policy row15_current=runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt \
  --checkpoint-policy row15_previous_alpha015=runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt \
  --checkpoint-policy previous_m1078_base=runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt \
  --checkpoint-policy short61049=runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt \
  --checkpoint-policy short61050=runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt \
  --checkpoint-policy short61051=runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --outcome-csv runs/m1161_row15_promoted_margin_slack_outcome_seed116100/outcome_interventions.csv \
  --delay-steps 10 \
  --max-continuation-steps 60 \
  --max-candidates 1200 \
  --max-candidates-per-physical-pair 8 \
  --max-candidates-per-checkpoint-target 128 \
  --max-accepted-rows-per-physical-pair 20 \
  --target-min-physical-pairs 12 \
  --target-min-left-steps 6 \
  --target-min-targets 2 \
  --max-rows-per-pair-fraction 0.25 \
  --min-eligible-physical-pairs 12 \
  --max-candidate-pair-fraction 0.25 \
  --source-obstacle-distance-bucket-width 5.0 \
  --source-obstacle-lateral-bucket-width 1.0 \
  --target-normal-margins 0.0005,0.001,0.0025,0.005,0.01,0.02,0.04,0.08,0.12,0.16,0.20 \
  --half-width-inflations 0 \
  --min-normal-margin 0.0 \
  --max-normal-margin 0.20 \
  --min-margin-gap 0.02 \
  --report-variants wrong_matched_history,reset_hidden,zero_current_response,zero_action_history,delayed_history \
  --margin-bucket-width 0.005 \
  --control-checkpoint-label none \
  --device cpu \
  --run-dir runs/m1161_row15_promoted_margin_slack_surface_seed116100
```

## Acceptance Criteria

M1161 should pass only if the final source-balanced relocation summary
satisfies the primary margin-slack gate:

```text
accepted_wrong_history_rows >= 100
accepted_wrong_physical_pairs >= 12
accepted_wrong_left_steps >= 6
accepted_wrong_checkpoints >= 4
accepted_wrong_targets >= 2
accepted_wrong_normal_margin_buckets >= 3 at width 0.005
accepted_wrong_normal_margin_max >= 0.01
accepted_wrong_success_drop_fraction == 1.0
max_rows_per_physical_pair_fraction <= 0.25
control_accepted_wrong_rows == 0
source_budget_ready == true
training_started == false
ppo_used == false
promoted == false
private_holdout_used == false
```

The `accepted_wrong_normal_margin_max >= 0.01` rule is deliberate. It prevents
the refresh from passing on a surface made only of the known near-zero row15
repair rows.

## Failure Classification

If M1161 fails, classify the failure before any threshold change:

```text
row15_promoted_margin_slack_surface_refresh_source_budget_shortfall
row15_promoted_margin_slack_surface_refresh_sparse
row15_promoted_margin_slack_surface_refresh_margin_bucket_sparse
row15_promoted_margin_slack_surface_refresh_slack_shortfall
row15_promoted_margin_slack_surface_refresh_duplicate_dominated
row15_promoted_margin_slack_surface_refresh_wrong_history_insensitive
row15_promoted_margin_slack_surface_refresh_training_or_contract_artifact
```

If the only failure is `slack_shortfall`, the next step should be a diagnostic
bucket audit, not weaker thresholds in the same branch.

## Decision

```text
decision: row15_promoted_margin_slack_surface_refresh_design_admit_run
next: m1161-v4-public-base-row15-promoted-margin-slack-surface-refresh-run
```
