# M1277 Paper-Route Four-Wheel Source Intervention Materialization

## Summary

M1277 materializes preferred/rejected counterfactual artifacts from the M1273
four-wheel source corpus.

Decision:

```text
four_wheel_source_intervention_materialization_pass_route_to_result_audit
```

M1277 is infrastructure-valid:

```text
near_high_union_source_pairs: 38
near_high_union_intervention_rows: 76
family_balanced_source_pairs: 63
family_balanced_intervention_rows: 126
intervention_rows: 202
observation_rows: 202
action_sequence_rows: 29088
```

No training, PPO, checkpoint promotion, private holdout, actor-input expansion,
accepted-threshold relaxation, high-fidelity validation claim, paper-level
claim, driver-performance claim, or self-identification claim occurs in M1277.

## Commands

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_four_wheel_source_intervention_materialization.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.four_wheel_source_intervention_materialization --source-run-dir runs/m1271_four_wheel_source_viability_calibration_smoke --corpus-run-dir runs/m1273_four_wheel_source_corpus_export --run-dir runs/m1277_four_wheel_source_intervention_materialization
```

Validation:

```text
1 passed in 2.02s
```

## Artifacts

Primary artifacts:

```text
runs/m1277_four_wheel_source_intervention_materialization/summary.json
runs/m1277_four_wheel_source_intervention_materialization/intervention_rows.csv
runs/m1277_four_wheel_source_intervention_materialization/intervention_observations.csv
runs/m1277_four_wheel_source_intervention_materialization/intervention_action_sequences.csv
runs/m1277_four_wheel_source_intervention_materialization/source_pair_rows.csv
runs/m1277_four_wheel_source_intervention_materialization/materialization_limits.md
```

## Result

Summary:

```text
source_scenario_profile: viability_calibration
source_accepted_separable_pairs: 108
corpus_exported_accepted_rows: 108
near_high_union_source_pairs: 38
near_high_union_intervention_rows: 76
family_balanced_source_pairs: 63
family_balanced_intervention_rows: 126
source_pair_rows: 101
intervention_rows: 202
observation_rows: 202
action_sequence_rows: 29088
observation_dim: 72
```

Checks:

```text
observation_all_finite: true
preferred_success_fail_count: 0
preferred_margin_negative_count: 0
margin_gap_threshold: 0.02
margin_gap_below_threshold_count: 0
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

## Artifact Semantics

Each source pair creates two branch-conditioned intervention rows:

```text
condition A:
  preferred = best_candidate_A
  rejected = best_candidate_B

condition B:
  preferred = best_candidate_B
  rejected = best_candidate_A
```

`intervention_observations.csv` contains only:

```text
intervention_id
obs_0 ... obs_71
```

Fault labels, branch labels, candidate ids, source labels, and outcome labels
are not observation columns.

`intervention_rows.csv` contains source metadata and preferred/rejected outcome
metadata for offline artifact use only.

`intervention_action_sequences.csv` contains the preferred and rejected action
sequence for every intervention row:

```text
intervention_id
role
candidate_id
step
steer
throttle
brake
```

## Interpretation

M1277 advances the source evidence chain from:

```text
accepted source rows
```

to:

```text
explicit preferred/rejected branch-action-outcome artifacts with clean actor-view
observations.
```

It still does not prove:

```text
closed-loop driver performance;
actor history necessity;
self-identification;
sim-to-real validity;
high-fidelity dynamics validity.
```

## Decision

Do not train.

Do not run PPO.

Do not promote.

Do not integrate into actor/Gym yet.

Admit one result audit:

```text
m1278-paper-route-four-wheel-source-intervention-materialization-result-audit
```

M1278 should audit observation cleanliness, subset suitability, duplicated
source-pair semantics, preferred/rejected outcome quality, and whether the next
step should be replay construction, boundary retargeting, policy-side design,
or another source repair.
