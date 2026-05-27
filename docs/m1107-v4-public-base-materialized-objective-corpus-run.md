# M1107 V4 Public Base Materialized Objective Corpus Run

## Purpose

M1107 builds the `proof_current` boundary-outcome corpus from M1104 materialized
rows and runs auxiliary objective sanity.

This milestone does not train actor weights, run PPO, run replay, mine rows,
promote a checkpoint, use private holdout, or change actor inputs.

## Command

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.boundary_outcome_corpus_objective \
  --checkpoint-policy proof_current=runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --boundary-rows-csv runs/m1104_target_policy_materialization/proof_current_boundary_rows.csv \
  --run-dir runs/m1107_materialized_objective_corpus \
  --device cpu \
  --objective-device cpu \
  --delay-steps 10 \
  --min-margin-gap 0.0 \
  --max-rows-per-physical-pair 0 \
  --max-rows-per-target 0 \
  --optimization-seeds 110700,110701,110702
```

## Corpus Result

Corpus build passes the M1105 gate:

```text
corpus_rows: 68
physical_pairs: 14
targets: 3
success_drop_rows: 68
selected_source_rows: 68
action_reconstruction_error_max: 0.0
action_reconstruction_error_mean: 0.0
obs_dim: 72
hidden_dim: 128
act_dim: 3
```

Target counts:

```text
future_braking_deceleration: 34
future_lateral_accel_response: 2
future_yaw_response: 32
```

The corpus has fewer rows than M1104 because the existing corpus builder
deduplicates `boundary_geometry_key`, as expected and pre-registered in M1105.

## Objective Result

Objective sanity passes:

```text
objective_pass: true
seed_pass_count: 3
mean_val_combined_loss_improvement: 2.951631
min_val_combined_loss_improvement: 1.762006
mean_val_delta_loss_improvement: 4.031372
min_val_delta_loss_improvement: 2.852015
mean_val_pairwise_accuracy_after: 0.944444
min_val_pairwise_accuracy_after: 0.833333
```

Per-seed objective pass:

```text
110700: true
110701: true
110702: true
```

## Interpretation

M1107 shows that the materialized `proof_current` rows produce a valid
single-checkpoint boundary-outcome corpus and a learnable auxiliary objective.

This is not driver improvement, not PPO readiness, not a promotion, not private
generalization evidence, and not level3 anticipatory self-identification. It is
an objective-sanity pass on a public proof-surface-derived corpus.

## Decision

```text
materialized_objective_corpus_pass_route_to_result_audit
```

Next:

```text
m1108-v4-public-base-materialized-objective-result-audit
```

M1108 should audit whether this objective pass is strong enough to design a
guarded actor update, and what gates would be required before any update.

## Validation

Research validation:

```text
make research-validate
```

Result:

```text
research validation passed
```
