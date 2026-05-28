# M1322 Paper-Route Source Repair Corpus Export

## Summary

M1322 exported the M1320 seven-family source repair run into standard stratified
source-corpus artifacts.

Decision:

```text
source_repair_corpus_export_pass_route_to_expansion_plan
```

The export is clean:

```text
exported_accepted_rows: 216
near_boundary_rows: 39
high_regret_rows: 154
family_balanced_rows: 121
inactive_fault_family_count: 1
```

Global friction remains visible as an inactive blocker:

```text
global_friction_step->global_friction_step
```

No training, PPO, checkpoint promotion, private holdout, actor-input expansion,
threshold relaxation, high-fidelity claim, paper-level claim, or closed-loop
self-identification claim occurs in M1322.

## Commands

Focused export test:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_four_wheel_source_corpus_export.py
```

Result:

```text
1 passed in 0.99s
```

Export:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.four_wheel_source_corpus_export \
  --source-run-dir runs/m1320_inactive_source_family_repair_smoke \
  --run-dir runs/m1322_source_repair_corpus_export
```

## Artifacts

Primary artifacts:

```text
runs/m1322_source_repair_corpus_export/summary.json
runs/m1322_source_repair_corpus_export/all_accepted_source_rows.csv
runs/m1322_source_repair_corpus_export/near_boundary_source_rows.csv
runs/m1322_source_repair_corpus_export/high_regret_source_rows.csv
runs/m1322_source_repair_corpus_export/family_balanced_source_rows.csv
runs/m1322_source_repair_corpus_export/inactive_fault_families.csv
```

## Result

Summary:

```text
source_run_dir: runs/m1320_inactive_source_family_repair_smoke
source_scenario_profile: source_repair_v1
source_accepted_separable_pairs: 216
exported_accepted_rows: 216
near_boundary_rows: 39
high_regret_rows: 154
family_balance_cap: 21
family_balanced_rows: 121
inactive_fault_family_count: 1
```

Accepted family counts:

```text
single_wheel_grip_collapse: 62
steering_actuator_fault: 58
left_right_split_mu: 35
tire_blowout_like: 23
halfshaft_torque_loss: 22
single_wheel_brake_pull: 10
load_cg_perturbation: 6
```

Near-boundary family counts:

```text
left_right_split_mu: 10
single_wheel_grip_collapse: 10
steering_actuator_fault: 7
tire_blowout_like: 6
load_cg_perturbation: 6
```

High-regret family counts:

```text
single_wheel_grip_collapse: 40
left_right_split_mu: 32
steering_actuator_fault: 31
tire_blowout_like: 23
halfshaft_torque_loss: 18
single_wheel_brake_pull: 8
load_cg_perturbation: 2
```

## Interpretation

M1322 is a valid source-corpus export. It is not yet an admissible
source-history corpus and does not admit PPO.

The exported set is much broader than M1273:

```text
M1273 exported accepted rows: 108
M1273 accepted families: 3

M1322 exported accepted rows: 216
M1322 accepted families: 7
```

However, the exported rows still need a new expansion plan:

- M1322 has `216` accepted source rows, below the earlier M1314 target `240`;
- family balance may still be uneven;
- global friction remains inactive;
- no response-history materialization exists for this new source run.

The next plan should not reuse M1280 materialized history rows by `pair_id`
alone because pair ids can collide across source runs. For M1323, use a
nonexistent or empty history-run directory so the planner treats the M1322 rows
as not yet materialized.

## Guardrails

Reported guardrails:

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

## Next Milestone

Admit:

```text
m1323-paper-route-source-repair-corpus-expansion-plan
```

Scope:

```text
run source_history_corpus_expansion_plan on runs/m1322_source_repair_corpus_export;
use an empty/nonexistent history-run directory to avoid pair-id collision;
report target coverage, fold balance, and global-friction blocker status;
do not train;
do not run PPO;
do not promote.
```
