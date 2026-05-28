# M1329 Paper-Route Source Top-Up Additive Merge Export Design

## Summary

M1329 designs a no-policy merge/export tool for M1322 and M1327 source rows.

Decision:

```text
source_topup_additive_merge_export_design_admit_implementation
```

The next step should implement a small export tool, not train or materialize
source histories yet.

## Tool

Add:

```text
src/autodrift/source_topup_additive_merge_export.py
tests/test_source_topup_additive_merge_export.py
```

The tool should normalize and merge:

```text
base source export:
  runs/m1322_source_repair_corpus_export/all_accepted_source_rows.csv

top-up source run:
  runs/m1327_source_repair_topup_horizon_corrected_smoke/accepted_separable_pairs.csv
  runs/m1327_source_repair_topup_horizon_corrected_smoke/scenario_summary.csv
```

The base rows are already enriched by `four_wheel_source_corpus_export`. The
top-up rows should be enriched using the same logic:

```text
speed
min_own_margin
min_cross_regret
near_boundary_margin flags
high_regret flags
source_family
```

The implementation may reuse helpers from `four_wheel_source_corpus_export.py`
instead of duplicating enrichment logic.

## Source Identity

Every exported row must include:

```text
source_run_id
source_row_id
source_input_path
```

Rules:

```text
M1322 source_run_id = m1322_source_repair_corpus_export
M1322 source_row_id = pair_id from all_accepted_source_rows.csv

M1327 source_run_id = m1327_source_repair_topup_horizon_corrected_smoke
M1327 source_row_id = pair_id from accepted_separable_pairs.csv
```

The unique source identity is:

```text
source_run_id + source_row_id
```

Never use raw `pair_id` alone.

## Duplicate Diagnostics

The tool should not silently remove rows by a coarse semantic key.

It should write diagnostics:

```text
semantic_duplicate_groups.csv
```

A semantic duplicate key should include at least:

```text
condition_A_fault
condition_B_fault
fault_family_pair
severity_pair
corner_or_side_variant_pair
scenario_id
seed
obstacle_body_x
obstacle_body_y
obstacle_half_width
speed_bin
obstacle_timing_bin
scenario_curvature_bin
best_A_template
best_B_template
best_candidate_A
best_candidate_B
```

If duplicates exist, report them. Do not remove them automatically unless the
identity is also duplicated.

## Output Artifacts

M1330 should write:

```text
runs/m1330_source_topup_additive_merge_export/summary.json
runs/m1330_source_topup_additive_merge_export/all_accepted_source_rows.csv
runs/m1330_source_topup_additive_merge_export/near_boundary_source_rows.csv
runs/m1330_source_topup_additive_merge_export/high_regret_source_rows.csv
runs/m1330_source_topup_additive_merge_export/family_balanced_source_rows.csv
runs/m1330_source_topup_additive_merge_export/source_run_summary.csv
runs/m1330_source_topup_additive_merge_export/family_source_summary.csv
runs/m1330_source_topup_additive_merge_export/semantic_duplicate_groups.csv
runs/m1330_source_topup_additive_merge_export/inactive_or_undercovered_families.csv
```

Suggested family cap:

```text
family_cap: 40
```

Rationale:

```text
M1328 naive family counts suggest cap=40 can preserve enough diversity while
keeping dominant steering/brake/grip families bounded.
```

Expected cap-40 balanced row count before exact export:

```text
halfshaft 22 + split 37 + load 40 + brake 40 + grip 40 + steering 40 + blowout 31 = 250
```

This should be enough for a later expansion planner to meet the `240` target if
the merge/export schema is valid.

## M1330 Command

Proposed command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_source_topup_additive_merge_export.py

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.source_topup_additive_merge_export \
  --base-export-run-dir runs/m1322_source_repair_corpus_export \
  --topup-source-run-dir runs/m1327_source_repair_topup_horizon_corrected_smoke \
  --run-dir runs/m1330_source_topup_additive_merge_export \
  --family-cap 40
```

## M1330 Acceptance

M1330 should pass as infrastructure if:

```text
focused tests pass
summary.json exists
source_identity_duplicate_count == 0
merged_source_identity_rows >= 300
family_balanced_rows >= 240
accepted_fault_family_pairs >= 7
global friction is reported as missing
halfshaft undercoverage is reported
labels_enter_actor_input == false
training_started == false
ppo_used == false
promoted == false
private_holdout_used == false
actor_input_contract_changed == false
accepted_thresholds_relaxed == false
```

If family-balanced rows are below `240`, M1330 should route to a result audit
instead of materialization.

## Next After M1330

If merge/export passes, the next route is not PPO. The next route is a fresh
corpus expansion plan:

```text
m1331-paper-route-source-topup-merged-corpus-expansion-plan
```

That plan should decide whether the merged export is admissible for
source-history materialization.

## Guardrails

M1329 changes no policy behavior:

```text
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
accepted_thresholds_relaxed: false
high_fidelity_validation_claimed: false
```

Allowed claim:

```text
M1329 designs a no-policy additive merge/export implementation.
```

Not allowed:

```text
merged corpus exists;
source-history materialization is admitted;
driver performance improved;
closed-loop self-identification is proven;
PPO or promotion is admitted.
```

## Next Milestone

Admit:

```text
m1330-paper-route-source-topup-additive-merge-export
```

Scope:

```text
implement merge/export tool and focused tests;
run one no-policy merge/export;
write result artifacts and diagnostics;
do not materialize histories;
do not train;
do not run PPO;
do not promote.
```
