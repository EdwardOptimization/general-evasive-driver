# M1088 V4 Public Base Source-Balanced Boundary Existing-Artifact Smoke

## Purpose

M1088 runs the M1086 source-balanced boundary accounting path on existing M1083
CSV artifacts only.

This milestone does not train, run PPO, promote a checkpoint, use private
holdout, rerun matched-current mining, or rerun boundary relocation.

## Inputs

Existing M1083 artifacts:

```text
runs/m1083_proof_hardened_retarget_outcome_seed108200/outcome_interventions.csv
runs/m1083_proof_hardened_retarget_boundary_surface_seed108200/boundary_relocation_rows.csv
```

Output run:

```text
runs/m1088_source_balanced_boundary_existing_artifact_smoke
```

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.source_balanced_boundary_relocation_surface \
  --candidate-csv runs/m1083_proof_hardened_retarget_outcome_seed108200/outcome_interventions.csv \
  --boundary-rows-csv runs/m1083_proof_hardened_retarget_boundary_surface_seed108200/boundary_relocation_rows.csv \
  --max-candidates 512 \
  --max-candidates-per-physical-pair 8 \
  --max-candidates-per-checkpoint-target 64 \
  --max-accepted-rows-per-physical-pair 20 \
  --target-min-physical-pairs 10 \
  --target-min-left-steps 5 \
  --target-min-targets 2 \
  --max-rows-per-pair-fraction 0.25 \
  --min-eligible-physical-pairs 10 \
  --max-candidate-pair-fraction 0.25 \
  --source-obstacle-distance-bucket-width 5.0 \
  --source-obstacle-lateral-bucket-width 1.0 \
  --margin-bucket-width 0.005 \
  --control-checkpoint-label none \
  --run-dir runs/m1088_source_balanced_boundary_existing_artifact_smoke
```

## Results

Source budget before boundary relocation is adequate:

```text
candidate_wrong_history_rows: 7257
eligible_physical_pairs: 371
eligible_left_steps: 28
eligible_checkpoints: 4
eligible_targets: 3
max_candidate_pair_rows: 32
max_candidate_pair_fraction: 0.004409535620779937
source_budget_ready: true
decision: source_budget_ready
```

The source-balanced selector also finds a diverse candidate set from the
existing outcome CSV:

```text
selected_rows: 512
selected_physical_pairs: 370
selected_left_steps: 28
selected_targets: 3
max_selected_rows_per_physical_pair: 3
max_selected_pair_fraction: 0.005859375
decision: source_balanced_candidates_ready
```

But the already-generated M1083 boundary relocation rows remain export-limited:

```text
balanced_exportable_rows: 102
accepted_wrong_rows: 102
accepted_wrong_physical_pairs: 6
accepted_wrong_left_steps: 5
accepted_wrong_checkpoints: 4
accepted_wrong_targets: 2
accepted_wrong_normal_margin_buckets: 4
accepted_wrong_success_drop_fraction: 1.0
max_rows_per_physical_pair_fraction: 0.19607843137254902
decision: reject_duplicate_dominated_boundary_surface
passed: false
```

Only one robustness gate fails:

```text
accepted_wrong_physical_pairs: 6 < 10
```

The existing outcome CSV does not carry usable source-obstacle geometry for
source-obstacle bucketing, so the smoke reports one `x=nan|y=nan` obstacle
bucket. This does not affect the physical-pair robustness decision, but it
means source-obstacle diversity cannot be audited from the existing outcome
artifact alone.

## Interpretation

M1088 separates two failure modes:

```text
pre-boundary source budget: ready
existing accepted boundary export: still source-limited
```

This means the current blocker is not that M1083 failed to mine enough
wrong-history candidates. It mined 371 eligible physical pairs and the new
selector can choose 512 candidates across 370 physical pairs.

The blocker is that the old M1083 boundary relocation artifact was generated
before source-balanced candidate selection existed. Once the accepted
near-boundary/success-drop window is applied, the export still collapses to six
physical pairs. Post-filtering cannot create the missing four physical pairs.

## Decision

```text
source_balanced_existing_artifact_smoke_export_limited_route_to_relocation_run_design
```

Next:

```text
m1089-v4-public-base-source-balanced-relocation-run-design
```

M1089 should design the next source-balanced relocation path. It should route
selected source-balanced candidates into the relocation evaluation itself,
preserve the existing robustness thresholds, and keep raw plus balanced
artifacts for audit. It should not convert the old M1083 accepted rows into a
protected/preference corpus.

## Guardrails

```text
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
full_new_mining_run: false
```
