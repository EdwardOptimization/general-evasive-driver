# M1144 V4 Public Base Row15 Promoted Objective Corpus Run

## Purpose

M1144 builds the `row15_current` boundary-outcome corpus from M1142
materialized rows and runs auxiliary objective sanity.

This milestone does not train actor weights, run PPO, run replay, mine rows,
promote a checkpoint, use private holdout, or change actor inputs.

## Command

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.boundary_outcome_corpus_objective \
  --checkpoint-policy row15_current=runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --boundary-rows-csv runs/m1142_row15_promoted_target_materialization/row15_current_boundary_rows.csv \
  --run-dir runs/m1144_row15_promoted_objective_corpus \
  --device cpu \
  --objective-device cpu \
  --delay-steps 10 \
  --min-margin-gap 0.0 \
  --max-rows-per-physical-pair 0 \
  --max-rows-per-target 0 \
  --optimization-seeds 114400,114401,114402
```

## Corpus Result

Corpus build passes the M1143 gate:

```text
corpus_rows: 76
physical_pairs: 13
targets: 2
success_drop_rows: 76
selected_source_rows: 76
action_reconstruction_error_max: 0.0
action_reconstruction_error_mean: 0.0
obs_dim: 72
hidden_dim: 128
act_dim: 3
```

Target counts:

```text
future_braking_deceleration: 52
future_yaw_response: 24
```

The corpus has fewer rows than M1142 because the existing corpus builder
deduplicates `boundary_geometry_key`, as expected and pre-registered in M1143.

## Objective Result

Objective sanity passes:

```text
objective_pass: true
seed_pass_count: 3
mean_val_combined_loss_improvement: 3.211031
min_val_combined_loss_improvement: 2.906849
mean_val_delta_loss_improvement: 4.054106
min_val_delta_loss_improvement: 3.633356
mean_val_pairwise_accuracy_after: 1.0
min_val_pairwise_accuracy_after: 1.0
```

Per-seed objective pass:

```text
114400: true
114401: true
114402: true
```

## Artifacts

```text
runs/m1144_row15_promoted_objective_corpus/boundary_outcome_corpus.csv
runs/m1144_row15_promoted_objective_corpus/boundary_outcome_corpus.npz
runs/m1144_row15_promoted_objective_corpus/selected_boundary_rows.csv
runs/m1144_row15_promoted_objective_corpus/corpus_summary.json
runs/m1144_row15_promoted_objective_corpus/objective_summary.json
runs/m1144_row15_promoted_objective_corpus/objective_seed_summary.csv
runs/m1144_row15_promoted_objective_corpus/objective_loss_summary.csv
runs/m1144_row15_promoted_objective_corpus/manifest.json
```

## Interpretation

M1144 shows that the `row15_current` materialized rows produce a valid
single-checkpoint boundary-outcome corpus and a learnable auxiliary objective.

This is not driver improvement, not PPO readiness, not a promotion, not private
generalization evidence, and not level3 anticipatory self-identification. It is
an objective-sanity pass on a public proof-surface-derived corpus.

## Decision

```text
row15_promoted_objective_corpus_pass_route_to_result_audit
```

Next:

```text
m1145-v4-public-base-row15-promoted-objective-result-audit
```

M1145 should audit whether this objective pass is strong enough to design a
guarded actor update, and what gates would be required before any update.
