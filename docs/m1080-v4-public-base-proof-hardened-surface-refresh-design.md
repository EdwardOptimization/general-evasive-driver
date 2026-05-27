# M1080 V4 Public Base Proof Hardened Surface Refresh Design

## Purpose

M1080 designs a fresh source-diverse protected/preference surface refresh for
the M1078 public-gate base before any new medium-PPO proposal.

This milestone does not mine rows, train, run PPO, promote, or use private
holdout.

## Current Base

```text
runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
```

The refresh should treat this as the primary current policy.

## Refresh Family

Use the new public base plus nearby family checkpoints:

```text
proof_hardened_current:
  runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt

short61049_previous:
  runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt

short61050_repeat:
  runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt

short61051_repeat:
  runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt
```

The repeats are not new bases. They provide source diversity and prevent the
refresh from overfitting only to the M1072/M1073 active rows.

## Why Refresh

M1078 promoted a proof-hardened public base after several public-gate repairs.
That is valid for a public-gate base, but the next PPO proposal should not use
only the old active rows. The project needs fresh current-base wrong-history
boundary rows mined under the promoted checkpoint.

## M1081 Pipeline

M1081 should run four stages.

### 1. Matched-Current Ambiguity Mining

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.matched_current_response_ambiguity \
  --checkpoint-policy proof_current=runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt \
  --checkpoint-policy short61049=runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt \
  --checkpoint-policy short61050=runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt \
  --checkpoint-policy short61051=runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --probe-seeds 108100,108101,108102,108103 \
  --episodes 40 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 1400 \
  --nearest-k 12 \
  --max-visible-quantile 0.05 \
  --min-target-z-delta 1.0 \
  --max-pairs-per-target 360 \
  --max-pairs-per-physical-pair 1 \
  --max-pairs-per-left-step 20 \
  --max-pairs-per-source-obstacle-bucket 40 \
  --obstacle-distance-bucket-width 5.0 \
  --obstacle-lateral-bucket-width 1.0 \
  --min-accepted-pairs 80 \
  --device cpu \
  --run-dir runs/m1081_proof_hardened_matched_current_seed108100
```

### 2. Matched-History Outcome Gate

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.matched_history_outcome_gate \
  --checkpoint-policy proof_current=runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt \
  --checkpoint-policy short61049=runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt \
  --checkpoint-policy short61050=runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt \
  --checkpoint-policy short61051=runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --pairs-csv runs/m1081_proof_hardened_matched_current_seed108100/matched_pairs.csv \
  --delay-steps 10 \
  --max-continuation-steps 60 \
  --min-margin-gap 0.02 \
  --max-pairs-per-checkpoint-target 0 \
  --pair-label-mode matching \
  --device cpu \
  --run-dir runs/m1081_proof_hardened_outcome_seed108100
```

### 3. Boundary Relocation

Use low-margin targets because the proof surfaces are near-boundary:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.wrong_history_boundary_relocation_surface \
  --checkpoint-policy proof_current=runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt \
  --checkpoint-policy short61049=runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt \
  --checkpoint-policy short61050=runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt \
  --checkpoint-policy short61051=runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --outcome-csv runs/m1081_proof_hardened_outcome_seed108100/outcome_interventions.csv \
  --delay-steps 10 \
  --max-continuation-steps 60 \
  --max-pairs-per-checkpoint-target 0 \
  --min-base-action-distance 0.0 \
  --target-normal-margins 0.0005,0.001,0.0025,0.005,0.01,0.02,0.05,0.10,0.15,0.20 \
  --half-width-inflations 0 \
  --min-normal-margin 0.0 \
  --max-normal-margin 0.20 \
  --min-margin-gap 0.02 \
  --min-accepted-wrong-rows 40 \
  --report-variants wrong_matched_history,reset_hidden,zero_current_response,zero_action_history,delayed_history \
  --device cpu \
  --run-dir runs/m1081_proof_hardened_boundary_surface_seed108100
```

### 4. Robustness Gates

Run robustness at three bucket widths:

```text
0.0100 diagnostic coarse bucket
0.0050 primary acceptance bucket
0.0025 diagnostic fine bucket
```

Primary acceptance uses `0.0050` to avoid repeating the M1055 coarse-bucket
artifact.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.boundary_wrong_history_surface_robustness \
  --boundary-rows-csv runs/m1081_proof_hardened_boundary_surface_seed108100/boundary_relocation_rows.csv \
  --control-checkpoint-label none \
  --margin-bucket-width 0.005 \
  --min-accepted-wrong-rows 80 \
  --min-physical-pairs 10 \
  --min-left-steps 5 \
  --min-checkpoints 3 \
  --min-targets 2 \
  --min-margin-buckets 2 \
  --min-success-drop-fraction 1.0 \
  --max-rows-per-pair-fraction 0.25 \
  --max-control-accepted-rows 0 \
  --run-dir runs/m1081_proof_hardened_boundary_robustness_w005_seed108100
```

## Acceptance Criteria

M1081 passes only if the primary `0.005` robustness gate passes:

```text
accepted_wrong_history_rows >= 80
physical_pairs >= 10
left_steps >= 5
checkpoints >= 3
targets >= 2
margin_buckets >= 2 at width 0.005
success_drop_fraction == 1.0
max_rows_per_pair_fraction <= 0.25
control_accepted_rows == 0
training_started == false
ppo_used == false
promoted == false
private_holdout_used == false
```

If the surface is strong but bucket-sensitive, classify explicitly instead of
loosening thresholds after the fact.

## Result Classes

```text
proof_hardened_surface_refresh_pass
proof_hardened_surface_refresh_sparse
proof_hardened_surface_refresh_margin_bucket_sparse
proof_hardened_surface_refresh_duplicate_dominated
proof_hardened_surface_refresh_wrong_history_insensitive
proof_hardened_surface_refresh_training_or_contract_artifact
```

## Decision

```text
proof_hardened_surface_refresh_design_admit_m1081_refresh
```

Next:

```text
m1081-v4-public-base-proof-hardened-surface-refresh
```
