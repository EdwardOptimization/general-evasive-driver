# M1054 V4 Public Base Post Short-Promotion Surface Refresh Design

## Purpose

M1054 designs a current-base source-diverse protected/preference surface
refresh after M1052 promoted the 4096-step guarded PPO checkpoint.

This milestone does not run mining, train, run PPO, use private holdout, change
actor inputs, or promote a checkpoint.

## Base And Family

Current public-gate base:

```text
runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt
```

Refresh family:

```text
short61049_current:
  runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt

short61050_repeat:
  runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt

short61051_repeat:
  runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt
```

Diagnostic previous base:

```text
m1044_previous_public_base:
  runs/ppo_m1044_combined_active_set_guarded_smoke_seed61044/checkpoint.pt
```

The refresh should use the three 4096-step family checkpoints as primary
policies and keep the previous base only as a diagnostic/control, not as a
requirement for accepting the new current-family surface.

## Why Refresh Before Medium PPO

M1049-M1052 used known public proof surfaces and active-set anchors. That is
valid for public-base promotion, but it is not enough evidence to lengthen PPO
again. Before medium PPO, the project should ask:

```text
Does the newly promoted short-PPO family still expose a source-diverse set of
wrong-history outcome boundaries that are not just the old row15/row16 public
singletons?
```

This follows the M266/M267 pattern:

```text
refresh protected surface first;
then convert to compact replay/objective corpus;
then use it as a gate for any further actor/PPO update.
```

## M1055 Pipeline

M1055 should run the refresh in four stages.

### 1. Matched-Current Ambiguity Mining

Command shape:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.matched_current_response_ambiguity \
  --checkpoint-policy short61049=runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt \
  --checkpoint-policy short61050=runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt \
  --checkpoint-policy short61051=runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --probe-seeds 105400,105401,105402,105403 \
  --episodes 40 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 1200 \
  --nearest-k 12 \
  --max-visible-quantile 0.05 \
  --min-target-z-delta 1.0 \
  --max-pairs-per-target 320 \
  --max-pairs-per-physical-pair 1 \
  --max-pairs-per-left-step 20 \
  --max-pairs-per-source-obstacle-bucket 40 \
  --obstacle-distance-bucket-width 5.0 \
  --obstacle-lateral-bucket-width 1.0 \
  --min-accepted-pairs 60 \
  --device cpu \
  --run-dir runs/m1055_post_short_promotion_matched_current_seed105400
```

### 2. Matched-History Outcome Gate

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.matched_history_outcome_gate \
  --checkpoint-policy short61049=runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt \
  --checkpoint-policy short61050=runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt \
  --checkpoint-policy short61051=runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --pairs-csv runs/m1055_post_short_promotion_matched_current_seed105400/matched_pairs.csv \
  --delay-steps 10 \
  --max-continuation-steps 60 \
  --min-margin-gap 0.02 \
  --max-pairs-per-checkpoint-target 0 \
  --pair-label-mode matching \
  --device cpu \
  --run-dir runs/m1055_post_short_promotion_outcome_seed105400
```

### 3. Boundary Relocation Surface

M1055 should include tighter low-margin windows than M266 because the promoted
base now has known near-cliff hard rows around `0.0005 m`:

```text
target-normal-margins:
  0.0005,0.001,0.0025,0.005,0.01,0.02,0.05,0.10,0.15,0.20
```

Command shape:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.wrong_history_boundary_relocation_surface \
  --checkpoint-policy short61049=runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt \
  --checkpoint-policy short61050=runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt \
  --checkpoint-policy short61051=runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --outcome-csv runs/m1055_post_short_promotion_outcome_seed105400/outcome_interventions.csv \
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
  --run-dir runs/m1055_post_short_promotion_boundary_surface_seed105400
```

### 4. Robustness Gate

Primary pass thresholds:

```text
accepted_wrong_history_rows >= 80
physical_pairs >= 10
left_steps >= 5
checkpoints >= 3
targets >= 2
margin_buckets >= 2
success_drop_fraction == 1.0
max_rows_per_pair_fraction <= 0.25
control_accepted_rows == 0
```

Command shape:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.boundary_wrong_history_surface_robustness \
  --boundary-rows-csv runs/m1055_post_short_promotion_boundary_surface_seed105400/boundary_relocation_rows.csv \
  --control-checkpoint-label none \
  --margin-bucket-width 0.01 \
  --min-accepted-wrong-rows 80 \
  --min-physical-pairs 10 \
  --min-left-steps 5 \
  --min-checkpoints 3 \
  --min-targets 2 \
  --min-margin-buckets 2 \
  --min-success-drop-fraction 1.0 \
  --max-rows-per-pair-fraction 0.25 \
  --max-control-accepted-rows 0 \
  --run-dir runs/m1055_post_short_promotion_boundary_robustness_seed105400
```

## Result Classes

M1055 should classify the result as:

```text
post_short_promotion_surface_refresh_pass
post_short_promotion_surface_refresh_sparse
post_short_promotion_surface_refresh_duplicate_dominated
post_short_promotion_surface_refresh_wrong_history_insensitive
post_short_promotion_surface_refresh_training_or_contract_artifact
```

## Acceptance Meaning

If M1055 passes, it does not admit PPO directly. It only admits M1056:

```text
convert refreshed current-base surface into compact replay/objective corpora.
```

If M1055 is sparse but non-empty, route to a sampling retarget design instead
of loosening thresholds silently.

If the surface is duplicate-dominated or wrong-history-insensitive, stop medium
PPO and audit public-gate overfit.

## Decision

```text
post_short_promotion_surface_refresh_design_admit_m1055_refresh
```

Next:

```text
m1055-v4-public-base-post-short-promotion-surface-refresh
```
