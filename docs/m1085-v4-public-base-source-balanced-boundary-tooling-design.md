# M1085 V4 Public Base Source-Balanced Boundary Tooling Design

## Purpose

M1085 designs the next tooling step after M1083 fixed wrong-history
success-drop quality but still failed the primary robustness gate on
physical-pair diversity.

This milestone does not train, run PPO, mine new rows, promote a checkpoint, or
use private holdout.

## Starting Evidence

The current public-gate base remains:

```text
runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
```

M1083 produced a strong raw wrong-history boundary signal:

```text
boundary accepted wrong-history rows: 626
wrong-history success-drop count: 626
success-drop fraction: 1.0
accepted source pairs: 71
accepted reset rows: 977
accepted zero-current rows: 862
```

But the primary `0.005m` robustness gate rejected it:

```text
accepted_wrong_physical_pairs: 6 < 10
max_rows_per_physical_pair_fraction: 0.3067092652 > 0.25
decision: reject_duplicate_dominated_boundary_surface
```

M1084 therefore closed `proof_hardened_base_surface_refresh` and opened
`source_balanced_boundary_tooling`.

## Diagnosis

The current boundary tooling has three stages:

```text
matched-current ambiguity mining
  -> outcome intervention gate
  -> wrong-history boundary relocation
  -> post-hoc robustness gate
```

This detects duplicate domination only after the expensive boundary relocation
stage has already produced rows. It can report the failure, but it cannot steer
the export away from repeated rows from the same physical pair.

Pure post-filtering is insufficient. M1083 has only six robustness physical
pairs in the accepted wrong-history set, so a post-filter cannot satisfy
`min_physical_pairs >= 10` without fabricating diversity or weakening the gate.

The missing capability is a source-balanced boundary export path that controls
source coverage before and during boundary evaluation.

## Required Tooling Semantics

M1086 should implement source-balanced boundary tooling with these semantics.

1. Preserve the current robustness thresholds:

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

2. Distinguish three different source concepts:

```text
matched_current_pair:
  source pair from matched-current ambiguity mining.

boundary_source_pair:
  candidate row entering boundary relocation.

robustness_physical_pair:
  left_seed:left_step:right_seed:right_step key used by the robustness gate.
```

The robustness gate remains authoritative. The new tooling may add earlier
diagnostics and quotas, but it must not redefine success by a different source
key.

3. Add a pre-boundary source budget report from the outcome CSV:

```text
candidate_wrong_history_rows
eligible_physical_pairs
eligible_left_steps
eligible_checkpoints
eligible_targets
eligible_source_obstacle_buckets
max_candidate_pair_fraction
per_physical_pair_candidate_counts
per_checkpoint_target_candidate_counts
```

This report answers whether enough potential source diversity exists before
relocation. If fewer than ten eligible physical pairs exist at this stage, the
tool should fail early with a sampling/blocker diagnosis instead of spending a
full relocation run.

4. Add source-balanced candidate selection before relocation:

```text
primary grouping:
  physical_pair_key = left_seed:left_step:right_seed:right_step

secondary coverage:
  checkpoint_label
  target
  left_step
  source_obstacle_bucket, if present

ordering within each group:
  larger margin_gap
  larger first_action_distance
  smaller visible_distance, if present
  deterministic tie-breakers
```

Selection should use round-robin or quota-limited traversal across physical
pairs, not a global top-K. The global top-K path is exactly what allows a few
high-scoring pairs to dominate.

5. Add relocation-time budget accounting:

```text
max_boundary_rows_per_physical_pair
max_accepted_rows_per_physical_pair
max_candidates_per_checkpoint_target
target_min_physical_pairs
target_min_left_steps
target_min_targets
```

The tool should continue evaluating rows after one source pair has enough
accepted rows, instead of letting that pair consume the run budget. If an
accepted-row cap is hit for a pair, additional rows from that pair may still be
written as diagnostics but must be marked non-exportable for corpus conversion.

6. Emit both raw and balanced artifacts:

```text
source_budget_summary.json
source_budget_rows.csv
balanced_candidate_rows.csv
boundary_relocation_rows.csv
accepted_wrong_history_rows.csv
balanced_accepted_wrong_history_rows.csv
balance_rejection_rows.csv
surface_summary.csv
summary.json
```

The raw rows preserve auditability. The balanced accepted rows are the only
rows eligible for conversion into a protected/preference corpus.

## Proposed M1086 Implementation Shape

M1086 should extend the existing boundary relocation path rather than replace
the robustness gate.

Candidate implementation:

```text
src/autodrift/source_balanced_boundary_relocation_surface.py
```

It can reuse:

```text
select_wrong_history_candidates
collect_requested_outcome_snapshots
build_boundary_relocation_rows
accepted_wrong_history_rows
add_robustness_keys
summarize_surface
```

The new module should expose small testable functions:

```text
physical_pair_key(row)
source_obstacle_bucket(row, distance_width, lateral_width)
build_source_budget(frame, margin_bucket_width)
select_source_balanced_candidates(frame, quotas)
mark_balanced_export_rows(boundary_rows, quotas)
classify_source_balance_export(summary, thresholds)
```

The CLI should accept the same checkpoint/env/outcome/relocation options as
`wrong_history_boundary_relocation_surface`, plus explicit source-balance
options:

```text
--target-min-physical-pairs 10
--max-candidates-per-physical-pair 8
--max-accepted-rows-per-physical-pair 20
--max-accepted-fraction-per-physical-pair 0.25
--min-eligible-physical-pairs 10
--source-obstacle-distance-bucket-width 5.0
--source-obstacle-lateral-bucket-width 1.0
```

The default behavior should be fail-closed: if the source budget does not show
enough eligible physical pairs, or if balanced export still fails the existing
robustness thresholds, the decision remains rejection.

## M1086 Acceptance Criteria

M1086 should be infrastructure/tooling only. It may run unit tests and a tiny
synthetic smoke if needed, but it should not run the full M1083 mining pipeline.

Acceptance criteria:

```text
1. Adds tested source-budget and source-balanced selection helpers.
2. Preserves current robustness thresholds.
3. Produces raw and balanced export artifact schema.
4. Fails early when eligible physical-pair diversity is insufficient.
5. Rejects surfaces that only pass after weakening thresholds.
6. Does not train, run PPO, mine new research rows, promote, or use private holdout.
```

## What M1085 Falsifies

M1085 rejects the route of simply post-filtering M1083. The accepted M1083 set
has only six physical pairs, so post-filtering cannot meet the ten-pair
robustness threshold.

M1085 also rejects another sampling-only retarget as the immediate next step.
The repeated M1081/M1083 failure pattern says the tool needs to control source
balance during export before another full surface run is worth doing.

## Decision

```text
source_balanced_boundary_tooling_design_admit_m1086_implementation
```

Next:

```text
m1086-v4-public-base-source-balanced-boundary-tooling-implementation
```
