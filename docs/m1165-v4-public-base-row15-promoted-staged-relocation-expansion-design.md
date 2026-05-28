# M1165 V4 Public Base Row15 Promoted Staged Relocation Expansion Design

## Purpose

M1165 redesigns the M1164 relocation expansion into a small, resource-bounded
pilot.

This milestone is design-only. It does not run relocation, run mining, rerun
the outcome gate, train actor weights, run PPO, promote, use private holdout,
or change actor inputs.

## Why Stage The Expansion

M1164 attempted a broad body-offset relocation expansion:

```text
max_candidates: 1600
target margins: 11
body offsets: 3 x 3
report variants: 5
max continuation steps: 60
```

It was interrupted after roughly `33` minutes with no summary artifact. That
does not prove the expansion is scientifically useless; it proves the resource
scope was too large for the current loop.

## Pilot Strategy

M1166 should run a small pilot over the existing M1161 outcome CSV:

```text
input:
  runs/m1161_row15_promoted_margin_slack_outcome_seed116100/outcome_interventions.csv

max_candidates: 240
max_candidates_per_physical_pair: 4
max_candidates_per_checkpoint_target: 64
target margins: 0.001,0.0025,0.005,0.01,0.02
body longitudinal offsets: -1.0,0.0,1.0
body lateral offsets: -0.3,0.0,0.3
report variants: wrong_matched_history only
```

The pilot is not allowed to convert a surface, claim pass/fail for the whole
branch, or weaken scientific thresholds. It only estimates whether body-offset
expansion improves the wrong-history accepted surface compared with M1161.

## M1166 Command

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
  --max-candidates 240 \
  --max-candidates-per-physical-pair 4 \
  --max-candidates-per-checkpoint-target 64 \
  --max-accepted-rows-per-physical-pair 20 \
  --target-min-physical-pairs 12 \
  --target-min-left-steps 6 \
  --target-min-targets 2 \
  --max-rows-per-pair-fraction 0.25 \
  --min-eligible-physical-pairs 12 \
  --max-candidate-pair-fraction 0.25 \
  --source-obstacle-distance-bucket-width 5.0 \
  --source-obstacle-lateral-bucket-width 1.0 \
  --target-normal-margins 0.001,0.0025,0.005,0.01,0.02 \
  --half-width-inflations 0 \
  --body-longitudinal-offsets=-1.0,0.0,1.0 \
  --body-lateral-offsets=-0.3,0.0,0.3 \
  --min-normal-margin 0.0 \
  --max-normal-margin 0.20 \
  --min-margin-gap 0.02 \
  --report-variants wrong_matched_history \
  --margin-bucket-width 0.005 \
  --control-checkpoint-label none \
  --device cpu \
  --run-dir runs/m1166_row15_promoted_staged_relocation_pilot_seed116100
```

## Diagnostic Criteria

M1166 is a pilot, not a conversion gate. It should report:

```text
summary exists
runtime completes
accepted_wrong_history_rows
accepted_wrong_physical_pairs
accepted_wrong_targets
accepted_wrong_normal_margin_buckets
accepted_wrong_normal_margin_max
max_rows_per_physical_pair_fraction
control_accepted_wrong_rows
```

Compare against M1161:

```text
M1161 accepted_wrong_history_rows: 15
M1161 accepted_wrong_physical_pairs: 2
M1161 accepted_wrong_targets: 1
M1161 accepted_wrong_normal_margin_buckets: 1
M1161 accepted_wrong_normal_margin_max: 0.002483
```

The pilot shows useful improvement if at least one of these is true:

```text
accepted_wrong_history_rows >= 5 within the smaller 240-candidate pilot
accepted_wrong_physical_pairs >= 2
accepted_wrong_normal_margin_buckets >= 2
accepted_wrong_normal_margin_max > 0.002483
```

Even if the pilot improves, it should route to a staged expansion design before
any conversion. If it does not improve, route to wrong-history mechanism audit.

## Decision

```text
decision: row15_promoted_staged_relocation_expansion_design_admit_pilot
next: m1166-v4-public-base-row15-promoted-staged-relocation-expansion-pilot
```
