# M1336 Paper-Route Materialized Source-History Objective Corpus Export

## Summary

M1336 implemented and ran the no-policy active/quarantine export for the
materialized source-history objective corpus.

Decision:

```text
materialized_source_history_objective_corpus_export_pass_route_to_result_audit
```

The export passes:

```text
active_source_pair_rows: 344
active_history_prefix_rows: 1376
active_history_frame_rows: 33024
active_history_intervention_rows: 1376
active_wrong_history_pair_rows: 1376
active_source_family_count: 6
active_zero_response_l2_prefix_count: 0
active_response_l2_ge_0_01_count: 1376
active_max_source_family_fold_share: 0.2985074627
quarantine_source_pair_rows: 22
quarantine_history_prefix_rows: 88
quarantine_history_frame_rows: 2112
quarantine_reasons: global_friction_missing, halfshaft_probe_silent
```

No training, PPO, promotion, private holdout, actor-input expansion, threshold
relaxation, or self-identification claim occurs in M1336.

## Implementation

Added:

```text
src/autodrift/materialized_source_history_objective_corpus_export.py
tests/test_materialized_source_history_objective_corpus_export.py
```

The tool filters M1333 materialized artifacts into:

```text
active rows:
  history-distinguishable non-halfshaft source pairs

quarantine rows:
  halfshaft rows with silent brake/lift response history
  global friction missing-family diagnostic
```

It does not rerun dynamics and does not evaluate a policy.

## Commands

Focused test:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_materialized_source_history_objective_corpus_export.py
```

Result:

```text
1 passed in 2.04s
```

Export:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.materialized_source_history_objective_corpus_export \
  --materialized-run-dir runs/m1333_source_topup_response_history_materialization \
  --run-dir runs/m1336_materialized_source_history_objective_corpus_export \
  --min-response-l2 0.01
```

## Artifacts

Primary artifacts:

```text
runs/m1336_materialized_source_history_objective_corpus_export/summary.json
runs/m1336_materialized_source_history_objective_corpus_export/active_source_pair_rows.csv
runs/m1336_materialized_source_history_objective_corpus_export/active_history_prefix_rows.csv
runs/m1336_materialized_source_history_objective_corpus_export/active_history_frame_rows.csv
runs/m1336_materialized_source_history_objective_corpus_export/active_history_intervention_rows.csv
runs/m1336_materialized_source_history_objective_corpus_export/active_wrong_history_pair_rows.csv
runs/m1336_materialized_source_history_objective_corpus_export/quarantine_source_pair_rows.csv
runs/m1336_materialized_source_history_objective_corpus_export/quarantine_history_prefix_rows.csv
runs/m1336_materialized_source_history_objective_corpus_export/quarantine_history_frame_rows.csv
runs/m1336_materialized_source_history_objective_corpus_export/quarantine_history_intervention_rows.csv
runs/m1336_materialized_source_history_objective_corpus_export/quarantine_wrong_history_pair_rows.csv
runs/m1336_materialized_source_history_objective_corpus_export/quarantine_family_rows.csv
runs/m1336_materialized_source_history_objective_corpus_export/active_family_summary.csv
runs/m1336_materialized_source_history_objective_corpus_export/active_fold_summary.csv
runs/m1336_materialized_source_history_objective_corpus_export/source_lineage_rows.csv
```

## Active Corpus

Active counts:

```text
source pairs: 344
history prefixes: 1376
history frames: 33024
history-intervention rows: 1376
wrong-history rows: 1376
```

Active family counts:

```text
left_right_split_mu: 37
load_cg_perturbation: 54
single_wheel_brake_pull: 62
single_wheel_grip_collapse: 64
steering_actuator_fault: 96
tire_blowout_like: 31
```

Active fold balance:

```text
fold 0: 71 pairs, 6 families, top share 0.2253521127
fold 1: 70 pairs, 6 families, top share 0.2857142857
fold 2: 68 pairs, 6 families, top share 0.2941176471
fold 3: 68 pairs, 6 families, top share 0.2941176471
fold 4: 67 pairs, 6 families, top share 0.2985074627
```

Response distinguishability:

```text
active_zero_response_l2_prefix_count: 0
active_response_l2_ge_0_01_count: 1376 / 1376
```

## Quarantine

Quarantine counts:

```text
quarantine_source_pair_rows: 22
quarantine_history_prefix_rows: 88
quarantine_history_frame_rows: 2112
quarantine_history_intervention_rows: 88
quarantine_wrong_history_pair_rows: 88
```

Quarantine family rows:

```text
halfshaft_torque_loss->halfshaft_torque_loss:
  quarantine_reason: halfshaft_probe_silent
  source_pair_rows: 22

global_friction_step->global_friction_step:
  quarantine_reason: global_friction_missing
  source_pair_rows: 0
```

## Identity And Guardrails

Identity:

```text
source_identity_duplicate_count: 0
source_identity_metadata_preserved: true
```

Guardrails:

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

## Interpretation

Supported:

```text
The M1333 materialized history corpus can be exported into a clean active
objective-corpus substrate plus explicit quarantine artifacts.
```

Supported:

```text
The active corpus has enough source-pair count, group count, family count,
fold balance, and response distinguishability for the next no-training objective
evaluator design.
```

Still unsupported:

```text
policy-side objective improvement;
actor update;
closed-loop PPO continuation;
promotion;
drive-sensitive halfshaft history probes;
global friction source coverage;
paper-level evidence;
strong self-identification.
```

## Decision

Do not train.

Do not run PPO.

Do not promote.

Admit one result audit:

```text
m1337-paper-route-materialized-source-history-objective-corpus-export-audit
```

M1337 should verify active/quarantine semantics and decide whether to route to
source-history objective evaluator design or export repair before any objective
update.
