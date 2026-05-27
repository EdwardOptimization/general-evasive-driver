# M1131 V4 Public Base Row15 Promoted Surface Refresh Design

## Purpose

M1131 designs a fresh source-diverse protected/preference surface refresh for
the M1129 alpha `0.15` public-gate base before any new PPO proposal.

This milestone is design-only. It does not mine rows, run replay, train actor
weights, run PPO, promote another checkpoint, use private holdout, or change
actor inputs.

## Current Base

```text
runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
```

The refresh should treat this as the primary current policy.

## Refresh Family

Use the new public base plus nearby public-family checkpoints:

```text
row15_current:
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

The non-current policies are not new bases. They provide source diversity and
prevent the refresh from overfitting only to M1120/M1123/M1127 active rows.

## Why Refresh

M1129 promoted a proof-hardened public base after several public-gate repairs.
That is valid for a public-gate base, but the next PPO proposal should not rely
only on the repaired row15 active set. The project needs fresh current-base
wrong-history boundary rows mined under alpha `0.15`.

M1131 therefore uses the later source-balanced boundary tooling rather than the
older direct M1080 relocation pipeline. The robustness thresholds remain
authoritative; source balancing only prevents duplicate dominance before and
during relocation.

## M1132 Pipeline

M1132 should run three stages.

### 1. Matched-Current Ambiguity Mining

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.matched_current_response_ambiguity \
  --checkpoint-policy row15_current=runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt \
  --checkpoint-policy previous_m1078_base=runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt \
  --checkpoint-policy short61049=runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt \
  --checkpoint-policy short61050=runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt \
  --checkpoint-policy short61051=runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --probe-seeds 113200,113201,113202,113203 \
  --episodes 40 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 1600 \
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
  --run-dir runs/m1132_row15_promoted_matched_current_seed113200
```

### 2. Matched-History Outcome Gate

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.matched_history_outcome_gate \
  --checkpoint-policy row15_current=runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt \
  --checkpoint-policy previous_m1078_base=runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt \
  --checkpoint-policy short61049=runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt \
  --checkpoint-policy short61050=runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt \
  --checkpoint-policy short61051=runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --pairs-csv runs/m1132_row15_promoted_matched_current_seed113200/matched_pairs.csv \
  --delay-steps 10 \
  --max-continuation-steps 60 \
  --min-margin-gap 0.02 \
  --max-pairs-per-checkpoint-target 0 \
  --pair-label-mode matching \
  --device cpu \
  --run-dir runs/m1132_row15_promoted_outcome_seed113200
```

### 3. Source-Balanced Boundary Relocation

Use the source-balanced relocation tool directly. It should preserve raw rows
for audit and export only source-balanced accepted wrong-history rows.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.source_balanced_boundary_relocation_surface \
  --checkpoint-policy row15_current=runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt \
  --checkpoint-policy previous_m1078_base=runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt \
  --checkpoint-policy short61049=runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt \
  --checkpoint-policy short61050=runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt \
  --checkpoint-policy short61051=runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --outcome-csv runs/m1132_row15_promoted_outcome_seed113200/outcome_interventions.csv \
  --delay-steps 10 \
  --max-continuation-steps 60 \
  --max-candidates 1024 \
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
  --target-normal-margins 0.0005,0.001,0.0025,0.005,0.01,0.02,0.05,0.10,0.15,0.20 \
  --half-width-inflations 0 \
  --min-normal-margin 0.0 \
  --max-normal-margin 0.20 \
  --min-margin-gap 0.02 \
  --report-variants wrong_matched_history,reset_hidden,zero_current_response,zero_action_history,delayed_history \
  --margin-bucket-width 0.005 \
  --control-checkpoint-label none \
  --device cpu \
  --run-dir runs/m1132_row15_promoted_source_balanced_surface_seed113200
```

## Acceptance Criteria

M1132 passes only if the source-balanced relocation summary satisfies the
primary `0.005m` acceptance gate:

```text
accepted_wrong_history_rows >= 100
accepted_wrong_physical_pairs >= 12
accepted_wrong_left_steps >= 6
accepted_wrong_checkpoints >= 4
accepted_wrong_targets >= 2
accepted_wrong_normal_margin_buckets >= 2 at width 0.005
accepted_wrong_success_drop_fraction == 1.0
max_rows_per_physical_pair_fraction <= 0.25
control_accepted_wrong_rows == 0
source_budget_ready == true
training_started == false
ppo_used == false
promoted == false
private_holdout_used == false
```

If the surface is strong but sparse, M1132 must classify the specific
shortfall instead of weakening thresholds after seeing the result.

## Result Classes

```text
row15_promoted_surface_refresh_pass
row15_promoted_surface_refresh_source_budget_shortfall
row15_promoted_surface_refresh_sparse
row15_promoted_surface_refresh_margin_bucket_sparse
row15_promoted_surface_refresh_duplicate_dominated
row15_promoted_surface_refresh_wrong_history_insensitive
row15_promoted_surface_refresh_training_or_contract_artifact
```

## Decision

```text
row15_promoted_surface_refresh_design_admit_m1132_refresh
```

Next:

```text
m1132-v4-public-base-row15-promoted-surface-refresh
```
