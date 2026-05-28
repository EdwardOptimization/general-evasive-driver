# M1273 Paper-Route Four-Wheel Source Corpus Export

## Summary

M1273 exports the M1271 accepted four-wheel source rows into stratified corpus
artifacts admitted by M1272.

Decision:

```text
four_wheel_source_corpus_export_pass_route_to_result_audit
```

M1273 is source-corpus infrastructure only:

```text
exported_accepted_rows: 108
near_boundary_rows: 19
high_regret_rows: 32
family_balanced_rows: 63
inactive_fault_family_count: 1
```

No training, PPO, checkpoint promotion, private holdout, actor-input expansion,
accepted-threshold relaxation, high-fidelity validation claim, paper-level
claim, or self-identification claim occurs in M1273.

## Commands

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_four_wheel_source_corpus_export.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.four_wheel_source_corpus_export --source-run-dir runs/m1271_four_wheel_source_viability_calibration_smoke --run-dir runs/m1273_four_wheel_source_corpus_export
```

Validation:

```text
1 passed in 0.91s
```

## Artifacts

Primary artifacts:

```text
runs/m1273_four_wheel_source_corpus_export/summary.json
runs/m1273_four_wheel_source_corpus_export/all_accepted_source_rows.csv
runs/m1273_four_wheel_source_corpus_export/near_boundary_source_rows.csv
runs/m1273_four_wheel_source_corpus_export/high_regret_source_rows.csv
runs/m1273_four_wheel_source_corpus_export/family_balanced_source_rows.csv
runs/m1273_four_wheel_source_corpus_export/inactive_fault_families.csv
```

## Result

Summary:

```text
source_scenario_profile: viability_calibration
source_accepted_separable_pairs: 108
exported_accepted_rows: 108
near_boundary_margin_threshold: 0.2
near_boundary_rows: 19
high_regret_margin_threshold: 0.05
high_regret_rows: 32
family_balance_cap: 21
family_balanced_rows: 63
inactive_fault_family_count: 1
```

Accepted family counts:

```text
left_right_split_mu->left_right_split_mu: 28
single_wheel_brake_pull->single_wheel_brake_pull: 59
single_wheel_grip_collapse->single_wheel_grip_collapse: 21
```

Near-boundary family counts:

```text
left_right_split_mu->left_right_split_mu: 7
single_wheel_brake_pull->single_wheel_brake_pull: 2
single_wheel_grip_collapse->single_wheel_grip_collapse: 10
```

High-regret family counts:

```text
left_right_split_mu->left_right_split_mu: 11
single_wheel_grip_collapse->single_wheel_grip_collapse: 21
```

Inactive fault families:

```text
halfshaft_torque_loss->halfshaft_torque_loss
```

## Corpus Semantics

`all_accepted_source_rows.csv` keeps all strict accepted M1271 rows and adds
derived fields:

```text
speed
min_own_margin
min_cross_regret
near_boundary_margin_le_0_05
near_boundary_margin_le_0_10
near_boundary_margin_le_0_20
high_regret_ge_0_05
high_regret_ge_0_10
source_family
```

`near_boundary_source_rows.csv` selects:

```text
min_own_margin <= 0.20
```

`high_regret_source_rows.csv` selects:

```text
min_cross_regret >= 0.05
```

`family_balanced_source_rows.csv` caps each accepted source family at `21`
rows, sorted by lower own margin first and higher cross-regret second.

`inactive_fault_families.csv` records fault-family pairs with zero accepted
rows. In M1273, halfshaft is viable but action-equivalent under the current
source lattice.

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

The export writes source metadata for offline research artifacts only. It does
not alter the main actor observation contract.

## Decision

Do not train.

Do not run PPO.

Do not promote.

Do not integrate into actor/Gym yet.

Admit one result audit:

```text
m1274-paper-route-four-wheel-source-corpus-export-result-audit
```

M1274 should decide whether to route next to boundary retargeting, intervention
design, corpus replay construction, or branch synthesis.
