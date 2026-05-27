# M1105 V4 Public Base Materialized Objective Corpus Design

## Purpose

M1105 designs the boundary-outcome corpus and objective-sanity run for the
M1104 `proof_current` materialized rows.

This milestone is design-only. It does not train actor weights, run PPO, run
replay, build a corpus, run objective sanity, mine rows, promote a checkpoint,
use private holdout, or change actor inputs.

## Inputs

Use:

```text
runs/m1104_target_policy_materialization/proof_current_boundary_rows.csv
```

with the single checkpoint policy:

```text
proof_current=runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
```

Environment:

```text
configs/m121_human_view_zero_obstacle_relvel.json
```

## Important Contract Detail

M1104 proof rows are raw-retained:

```text
materialized rows: 133
```

The existing `boundary_outcome_corpus_objective` intentionally drops duplicate
`boundary_geometry_key` rows before corpus construction. A read-only pre-audit
of the selector path indicates the expected deduplicated corpus input is:

```text
selected unique boundary rows: 68
physical pairs: 14
targets: 3
left steps: 9
source labels: 4
```

This is acceptable for objective sanity because M1104 remains the proof-surface
artifact. The objective corpus is an auxiliary learning-signal check, not a
replacement proof gate.

## Command

M1106 should run:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.boundary_outcome_corpus_objective \
  --checkpoint-policy proof_current=runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --boundary-rows-csv runs/m1104_target_policy_materialization/proof_current_boundary_rows.csv \
  --run-dir runs/m1106_materialized_objective_corpus \
  --device cpu \
  --objective-device cpu \
  --delay-steps 10 \
  --min-margin-gap 0.0 \
  --max-rows-per-physical-pair 0 \
  --max-rows-per-target 0 \
  --optimization-seeds 110600,110601,110602
```

Do not use any checkpoint other than `proof_current` in this first run.

## Corpus Gates

Corpus build passes only if:

```text
corpus_rows >= 60
physical_pairs >= 10
targets == 3
success_drop_rows == corpus_rows
selected_source_rows >= 60
action_reconstruction_error_max <= 0.005
action_reconstruction_error_mean <= 0.001
```

The row threshold is deliberately lower than the raw proof threshold because
the corpus builder deduplicates by geometry. This does not weaken M1104's proof
surface; it only defines whether the auxiliary objective has enough unique
examples to test.

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

If M1106 passes, it may claim:

```text
proof_current materialized rows can produce a valid single-checkpoint
boundary-outcome corpus and a learnable auxiliary objective.
```

It may not claim:

```text
driver improvement
checkpoint promotion
PPO readiness
private generalization
level3 anticipatory self-identification
```

## Decision

```text
materialized_objective_corpus_design_route_to_branch_synthesis
```

Next:

```text
m1106-v4-public-base-family-aggregate-conversion-synthesis
```

The workflow synthesis cadence has fired. The objective sanity run should be
pre-registered after M1106 synthesis opens the next branch.

## Validation

Research validation:

```text
make research-validate
```

Result:

```text
research validation passed
```
