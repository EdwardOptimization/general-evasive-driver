# M1143 V4 Public Base Row15 Promoted Objective Corpus Design

## Purpose

M1143 designs the boundary-outcome corpus and objective-sanity run for the
M1142 `row15_current` materialized rows.

This milestone is design-only. It does not build a corpus, run objective
sanity, run replay, train actor weights, run PPO, mine rows, promote a
checkpoint, use private holdout, or change actor inputs.

## Inputs

Use:

```text
runs/m1142_row15_promoted_target_materialization/row15_current_boundary_rows.csv
```

with the single checkpoint policy:

```text
row15_current=runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
```

Environment:

```text
configs/m121_human_view_zero_obstacle_relvel.json
```

## Read-Only Pre-Audit

M1142 materialized rows are raw-retained:

```text
raw materialized rows: 148
normal successes: 148
wrong-history successes: 0
success drops: 148
finite objective rows: 148
```

The existing `boundary_outcome_corpus_objective` deduplicates by
`boundary_geometry_key` before corpus construction. A read-only CSV audit of
the M1142 rows gives:

```text
unique boundary geometry rows: 76
physical pairs: 13
targets: 2
left steps: 6
source labels: 5
success-drop rows: 76
max rows per physical pair: 10
max rows per target: 52
```

Target counts after geometry deduplication:

```text
future_braking_deceleration: 52
future_yaw_response:         24
```

Source counts after geometry deduplication:

```text
previous_m1078_base: 5
row15_current:       13
short61049:          20
short61050:          16
short61051:          22
```

This is smaller than the raw proof surface but still large enough for an
auxiliary objective sanity run. The corpus is not a replacement proof gate.

## M1144 Command

M1144 should run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.boundary_outcome_corpus_objective \
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

Do not use any checkpoint other than `row15_current` in this first objective
sanity run.

## Corpus Gates

Corpus build passes only if:

```text
corpus_rows >= 70
physical_pairs >= 12
targets == 2
success_drop_rows == corpus_rows
selected_source_rows >= 70
action_reconstruction_error_max <= 0.005
action_reconstruction_error_mean <= 0.001
```

The row threshold is deliberately lower than the raw materialized row count
because the corpus builder deduplicates by geometry. This does not weaken
M1142's proof surface; it only checks whether the auxiliary objective has
enough unique examples to test.

## Objective-Sanity Gates

Use the existing objective summary rule:

```text
objective_pass == true
seed_pass_count == 3
min_val_combined_loss_improvement > 0
min_val_delta_loss_improvement > 0
mean_val_pairwise_accuracy_after >= 0.60
```

If objective sanity fails, record it as an auxiliary objective failure and do
not proceed to actor update. The failure should route to objective audit, not
threshold weakening.

## Allowed Claims

If M1144 passes, it may claim:

```text
row15_current materialized rows can produce a valid single-checkpoint
boundary-outcome corpus and a learnable auxiliary objective.
```

It may not claim:

```text
driver improvement
checkpoint promotion
PPO readiness
private generalization
paper-level evidence
level3 anticipatory self-identification
```

## Decision

```text
row15_promoted_objective_corpus_design_admit_objective_sanity_run
```

Next:

```text
m1144-v4-public-base-row15-promoted-objective-corpus-run
```
