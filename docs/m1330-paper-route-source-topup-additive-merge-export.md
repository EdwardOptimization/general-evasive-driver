# M1330 Paper-Route Source Top-Up Additive Merge Export

## Summary

M1330 implemented and ran the additive source merge/export tool.

Decision:

```text
source_topup_additive_merge_export_pass_route_to_expansion_plan
```

The export passes the pre-registered infrastructure gate:

```text
merged_source_identity_rows: 366
source_identity_duplicate_count: 0
semantic_duplicate_group_count: 0
family_balanced_rows: 250
accepted_fault_family_pairs: 7
```

This is a valid merged source-corpus export. It is not yet source-history
materialization and does not admit PPO or promotion. The next step is a fresh
corpus expansion plan on the merged export.

## Implementation

Added:

```text
src/autodrift/source_topup_additive_merge_export.py
tests/test_source_topup_additive_merge_export.py
```

Focused test:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_source_topup_additive_merge_export.py
```

Result:

```text
1 passed in 0.90s
```

## Export Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.source_topup_additive_merge_export \
  --base-export-run-dir runs/m1322_source_repair_corpus_export \
  --topup-source-run-dir runs/m1327_source_repair_topup_horizon_corrected_smoke \
  --run-dir runs/m1330_source_topup_additive_merge_export \
  --family-cap 40
```

## Result

Summary:

```text
base_exported_accepted_rows: 216
topup_accepted_separable_pairs: 150
merged_source_identity_rows: 366
source_identity_duplicate_count: 0
semantic_duplicate_group_count: 0
near_boundary_rows: 115
high_regret_rows: 228
family_balance_cap: 40
family_balanced_rows: 250
accepted_fault_family_pairs: 7
inactive_or_undercovered_family_count: 2
```

Family counts:

```text
single_wheel_grip_collapse: 64
steering_actuator_fault: 96
left_right_split_mu: 37
tire_blowout_like: 31
halfshaft_torque_loss: 22
single_wheel_brake_pull: 62
load_cg_perturbation: 54
```

Undercovered or missing:

```text
global_friction_step: 0 / 30, missing
halfshaft_torque_loss: 22 / 30, under target
```

## Identity Fix

M1330 does not preserve raw local `pair_id` values. It writes:

```text
pair_id: global merged pair id, 0..365
source_run_id: original source run
source_row_id: original row-local pair id
original_pair_id: original row-local pair id
source_identity: source_run_id + source_row_id
```

This is necessary because the expansion planner uses `pair_id` for fold
assignment and materialization tracking. Raw pair ids collide across source
runs.

## Artifacts

Primary artifacts:

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

## Interpretation

Supported:

```text
M1322 and M1327 can be merged into a source-run-identified corpus with enough
balanced rows for a fresh expansion plan.
```

Supported:

```text
M1327 materially repaired M1322 load/CG and brake asymmetry undercoverage.
```

Still not supported:

```text
global friction is solved;
halfshaft reaches the 30-row family target;
source-history materialization is admitted;
policy performance improved;
PPO or promotion is admitted.
```

## Guardrails

Guardrails held:

```text
labels_enter_actor_input: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
accepted_thresholds_relaxed: false
high_fidelity_validation_claimed: false
```

## Next Step

Admit:

```text
m1331-paper-route-source-topup-merged-corpus-expansion-plan
```

Scope:

```text
run source_history_corpus_expansion_plan on the M1330 merged export;
use an empty/nonexistent history-run directory to avoid stale materialized
history matches;
report target coverage, fold balance, halfshaft undercoverage, and global
friction blocker status;
do not materialize histories yet;
do not train;
do not run PPO;
do not promote.
```
