# M1086 V4 Public Base Source-Balanced Boundary Tooling Implementation

## Purpose

M1086 implements the source-balanced boundary tooling designed in M1085.

This milestone is infrastructure-only. It does not train, run PPO, promote a
checkpoint, use private holdout, or run a full new mining pipeline.

## Implemented Module

New module:

```text
src/autodrift/source_balanced_boundary_relocation_surface.py
```

The module adds reusable helper functions:

```text
physical_pair_key
source_obstacle_bucket
add_source_balance_keys
build_source_budget
select_source_balanced_candidates
mark_balanced_export_rows
write_source_balance_artifacts
run_source_balanced_boundary_artifact_smoke
```

The implementation preserves the robustness-gate physical-pair key:

```text
left_seed:left_step:right_seed:right_step
```

It does not redefine source diversity. It only adds earlier source-budget
diagnostics and balanced export marking before the existing robustness
thresholds are applied.

## Source-Budget Layer

`build_source_budget` reports candidate diversity before boundary relocation:

```text
candidate_wrong_history_rows
eligible_physical_pairs
eligible_left_steps
eligible_checkpoints
eligible_targets
eligible_source_obstacle_buckets
max_candidate_pair_rows
max_candidate_pair_fraction
source_budget_ready
```

This lets the harness fail early if the candidate pool cannot possibly satisfy
the physical-pair robustness threshold.

## Balanced Candidate Selection

`select_source_balanced_candidates` selects relocation candidates by
physical-pair round-robin instead of global top-K. It enforces caps for:

```text
max_candidates
max_candidates_per_physical_pair
max_candidates_per_checkpoint_target
target_min_physical_pairs
target_min_left_steps
target_min_targets
max_rows_per_pair_fraction
```

The focused test verifies that a globally top-scoring duplicate pair no longer
dominates the selected set.

## Balanced Export Marking

`mark_balanced_export_rows` keeps raw boundary rows for audit but marks which
accepted wrong-history rows are eligible for balanced export.

It writes a `balanced_exportable` flag and a `balance_rejection_reason`. Rows
past the per-physical-pair cap remain in the raw CSV but are not eligible for
corpus conversion.

The final decision still uses the existing robustness thresholds:

```text
min_accepted_wrong_rows: 80
min_physical_pairs: 10
min_left_steps: 5
min_checkpoints: 3
min_targets: 2
min_margin_buckets: 2
min_success_drop_fraction: 1.0
max_rows_per_pair_fraction: 0.25
max_control_accepted_rows: 0
```

## Existing-Artifact Smoke CLI

The module includes a light CLI:

```text
python -m autodrift.source_balanced_boundary_relocation_surface \
  --candidate-csv <outcome_interventions.csv> \
  --boundary-rows-csv <boundary_relocation_rows.csv> \
  --run-dir <run_dir>
```

This command only reads existing artifacts and writes source-budget/balanced
export diagnostics. It does not replay environments, mine rows, train, or run
PPO.

## Tests

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_source_balanced_boundary_relocation_surface.py \
  tests/test_wrong_history_boundary_relocation_surface.py \
  tests/test_boundary_wrong_history_surface_robustness.py
```

Result:

```text
20 passed
```

The tests cover:

```text
physical-pair key preservation
source obstacle bucketing
source-budget ready and fail-closed paths
round-robin balanced candidate selection
balanced export caps
six-physical-pair fail-closed behavior
artifact writer output
existing-artifact smoke runner
```

## Decision

```text
source_balanced_boundary_tooling_implementation_admit_existing_artifact_smoke
```

Next:

```text
m1087-v4-public-base-source-balanced-boundary-existing-artifact-smoke
```
