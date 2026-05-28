# M1280 Paper-Route Four-Wheel Source Response-History Materialization

## Summary

M1280 materializes branch-specific response histories and wrong-history swaps for
the M1277 near/high source interventions.

Decision:

```text
four_wheel_source_response_history_materialization_pass_route_to_result_audit
```

M1280 is infrastructure-valid:

```text
history_prefix_rows: 152
history_frame_rows: 3648
history_intervention_rows: 152
wrong_history_pair_rows: 152
wrong_history_valid_count: 152
```

No training, PPO, checkpoint promotion, private holdout, actor-input expansion,
accepted-threshold relaxation, high-fidelity validation claim, paper-level
claim, driver-performance claim, or self-identification claim occurs in M1280.

## Commands

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_four_wheel_source_response_history_materialization.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.four_wheel_source_response_history_materialization --source-run-dir runs/m1271_four_wheel_source_viability_calibration_smoke --intervention-run-dir runs/m1277_four_wheel_source_intervention_materialization --run-dir runs/m1280_four_wheel_source_response_history_materialization
```

Validation:

```text
1 passed in 2.04s
```

## Artifacts

Primary artifacts:

```text
runs/m1280_four_wheel_source_response_history_materialization/summary.json
runs/m1280_four_wheel_source_response_history_materialization/history_prefix_rows.csv
runs/m1280_four_wheel_source_response_history_materialization/history_frame_rows.csv
runs/m1280_four_wheel_source_response_history_materialization/history_intervention_rows.csv
runs/m1280_four_wheel_source_response_history_materialization/wrong_history_pair_rows.csv
```

## Result

Summary:

```text
near_high_union_intervention_rows: 76
probe_templates: left_brake_probe, right_brake_probe
history_length: 24
history_prefix_rows: 152
history_frame_rows: 3648
history_intervention_rows: 152
wrong_history_pair_rows: 152
wrong_history_valid_count: 152
```

Actor-view history:

```text
actor_view_history_column_count: 15
actor_view_history_all_finite: true
forbidden_actor_view_history_columns: []
```

Actor-view columns:

```text
cmd_steer
cmd_throttle
cmd_brake
vx
vy
yaw_rate
ax
ay
steer_state
steer_rate
drive_state
brake_state
prev_cmd_steer
prev_cmd_throttle
prev_cmd_brake
```

Distinguishability diagnostics:

```text
response_l2_mean: 0.2109745544
response_l2_min: 0.0157835288
response_l2_ge_0_01_count: 152
final_yaw_rate_diff_ge_0_01_count: 152
final_vy_diff_ge_0_01_count: 144
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

M1280 resolves the artifact-level blocker identified by M1278:

```text
same current source observation can require different actions,
but now each intervention can be paired with correct branch history or
same-pair wrong branch history.
```

This creates the substrate for future policy-side history tests:

```text
same current observation;
same preferred/rejected source relation;
correct response history versus wrong response history.
```

It still does not prove self-identification because no actor has consumed these
histories yet.

## Decision

Do not train.

Do not run PPO.

Do not promote.

Do not integrate into actor/Gym yet.

Admit one result audit:

```text
m1281-paper-route-four-wheel-source-response-history-materialization-result-audit
```

M1281 should audit response-history cleanliness, distinguishability, wrong
history semantics, and whether the next step is policy-side gate design,
history-prefix repair, or branch synthesis.
