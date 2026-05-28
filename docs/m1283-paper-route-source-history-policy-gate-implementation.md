# M1283 Paper-Route Source-History Policy Gate Implementation

## Summary

M1283 implements and runs the no-training source-history policy gate designed in
M1282.

Decision:

```text
source_history_policy_gate_implementation_pass_signal_weak_route_to_objective_design
```

The infrastructure is valid:

```text
row_count: 152
finite_row_count: 152
projection_rows: 152
projection_valid_count: 152
wrong_history_valid_count: 152
checkpoint_contract: canonical_72_human_view_online_recurrent
```

The policy-side action-level signal is weak:

```text
result_class: action_level_history_signal_weak
both_directional_fraction: 0.0
preferred_hidden_margin_positive_fraction: 0.4868421053
history_action_l2_mean: 0.0991899077
```

Interpretation:

```text
The source histories change the recurrent actor's action means, but the current
public-gate checkpoint does not use those histories in the desired
preferred/rejected direction on this four-wheel source corpus.
```

This is not a driver-performance result and not self-identification proof.

## Commands

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_source_history_policy_gate.py
```

Run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.source_history_policy_gate --checkpoint runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt --history-run-dir runs/m1280_four_wheel_source_response_history_materialization --intervention-run-dir runs/m1277_four_wheel_source_intervention_materialization --run-dir runs/m1283_source_history_policy_gate
```

Validation:

```text
2 passed in 0.89s
```

## Artifacts

Primary artifacts:

```text
src/autodrift/source_history_policy_gate.py
tests/test_source_history_policy_gate.py
runs/m1283_source_history_policy_gate/summary.json
runs/m1283_source_history_policy_gate/policy_gate_rows.csv
runs/m1283_source_history_policy_gate/history_projection_audit.csv
```

## Projection And Contract

Checkpoint:

```text
runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
```

Contract:

```text
checkpoint_actor_encoder: human_view_online_gru
checkpoint_contract: canonical_72_human_view_online_recurrent
```

Projection:

```text
M1280 history rows are projected into canonical 72-value actor frames.
response indices 0..11 are normalized according to docs/observation-contract.md.
context indices 12..71 are zero during prefix replay.
cmd_* fields are prefix action metadata, not appended actor observations.
```

Projection audit:

```text
projection_rows: 152
projection_valid_count: 152
all_projected_finite: true for all histories
zero_context_hidden_matches_current_context: true for all histories
```

The `history_projection_audit.csv` also confirms normalized actuator ranges:

```text
drive_state range: 0.0 to 0.0
brake_state range: 1.0 to 1.0
prev_throttle range: 0.0 to 0.0
prev_brake range: 1.0 to 1.0
```

## Policy Metrics

Rows:

```text
row_count: 152
finite_row_count: 152
condition A rows: 76
condition B rows: 76
left_brake_probe rows: 76
right_brake_probe rows: 76
```

Primary counts:

```text
correct_preference_positive_count: 76
wrong_history_preference_positive_count: 76
both_directional_count: 0
preferred_hidden_margin_positive_count: 74
rejected_hidden_margin_positive_count: 74
```

Primary fractions:

```text
both_directional_fraction: 0.0
preferred_hidden_margin_positive_fraction: 0.4868421053
```

Thresholds:

```text
both_directional_fraction >= 0.60
preferred_hidden_margin_positive_fraction >= 0.60
history_action_l2_mean >= 0.02
```

Only the action-L2 threshold passes:

```text
history_action_l2_min: 0.0038717205
history_action_l2_p10: 0.0052115729
history_action_l2_median: 0.0126349405
history_action_l2_p90: 0.4315552870
history_action_l2_mean: 0.0991899077
```

Log-probability margin distributions:

```text
correct_preference_margin median: -0.0038137436
wrong_history_preference_margin median: -0.0038137436
preferred_hidden_margin median: -0.0055847168
rejected_hidden_margin median: -0.0055847168
```

Directional structure:

```text
correct_preference_positive_count by condition:
  A: 46
  B: 30

wrong_history_preference_positive_count by condition:
  A: 30
  B: 46
```

Interpretation:

```text
The checkpoint exhibits condition/action asymmetry and nonzero hidden-induced
action movement, but not the desired bidirectional mapping:

correct history -> preferred action
wrong history   -> rejected action
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

M1283 does not mutate checkpoint weights. It only loads the checkpoint and runs
forward passes.

## Interpretation

Supported claim:

```text
The source-history policy gate is now implemented and can produce finite
correct-history versus wrong-history action-level metrics under the canonical
72-value human-view recurrent actor contract.
```

Unsupported claims:

```text
the current public-gate checkpoint uses M1280 histories correctly;
closed-loop source-history intervention works;
the driver has self-identification;
the four-wheel compact source pilot is high fidelity;
PPO or promotion is admitted.
```

The negative/weak signal is useful. It says the newly materialized four-wheel
source histories are not automatically understood by the existing public-gate
checkpoint. The next variable should be an exact source-history preference
objective or adapter, not PPO.

## Next Step

Admit design-only:

```text
m1284-paper-route-source-history-objective-design
```

M1284 should design an exact no-PPO source-history preference objective around
the M1283 gate:

```text
correct hidden should score preferred actions above rejected actions;
wrong hidden should score rejected actions above preferred actions;
the objective should be evaluated exactly on the full M1280/M1277 source corpus;
public proof-retention and branch-cadence guardrails must stay active;
no PPO or promotion should occur before objective-only sanity and later branch
synthesis.
```
