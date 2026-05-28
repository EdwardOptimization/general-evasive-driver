# M1271 Paper-Route Four-Wheel Source Viability Calibration Smoke

## Summary

M1271 runs the bounded no-policy four-wheel source viability calibration smoke
admitted by M1270.

Decision:

```text
four_wheel_source_viability_calibration_smoke_source_positive_route_to_result_audit
```

M1271 is infrastructure-valid and source-positive under unchanged strict source
acceptance:

```text
scenario_profile: viability_calibration
matched_pair_count: 720
action_rollouts: 15840
accepted_separable_pairs: 108
result_class: capability_separable_signal
source_positive: true
```

No training, PPO, checkpoint promotion, private holdout, actor-input expansion,
accepted-threshold relaxation, high-fidelity validation claim, paper-level
claim, or self-identification claim occurs in M1271.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_four_wheel_fault_source_shape.py tests/test_four_wheel_dynamics.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.four_wheel_fault_source_shape --scenario-profile viability_calibration --run-dir runs/m1271_four_wheel_source_viability_calibration_smoke
```

Validation:

```text
10 passed in 0.94s
```

## Artifacts

Primary artifacts:

```text
runs/m1271_four_wheel_source_viability_calibration_smoke/summary.json
runs/m1271_four_wheel_source_viability_calibration_smoke/scenario_summary.csv
runs/m1271_four_wheel_source_viability_calibration_smoke/snapshot_candidates.csv
runs/m1271_four_wheel_source_viability_calibration_smoke/action_lattice.csv
runs/m1271_four_wheel_source_viability_calibration_smoke/action_rollouts.csv
runs/m1271_four_wheel_source_viability_calibration_smoke/matched_capability_pairs.csv
runs/m1271_four_wheel_source_viability_calibration_smoke/accepted_separable_pairs.csv
runs/m1271_four_wheel_source_viability_calibration_smoke/rejected_pairs.csv
```

## Result

Summary:

```text
sequence_length: 72
dt: 0.02
min_best_action_l2: 0.12
min_cross_regret_margin: 0.02
scenario_count: 180
fault_count: 8
fault_pair_count: 4
matched_pair_count: 720
action_lattice_rows: 11
action_rollouts: 15840
accepted_separable_pairs: 108
rejected_pairs: 612
best_actions_diverged_pairs: 216
low_regret_pairs: 561
own_branch_viability_fail_count: 108
all_four_rollouts_collision_count: 91
unique_fault_family_pairs: 4
accepted_fault_family_pairs: 3
```

Compared with M1268:

```text
M1268 accepted_separable_pairs: 0
M1271 accepted_separable_pairs: 108

M1268 own_branch_viability_fail_count: 103 / 108
M1271 own_branch_viability_fail_count: 108 / 720

M1268 all_four_rollouts_collision_count: 103 / 108
M1271 all_four_rollouts_collision_count: 91 / 720
```

The blocker changed again:

```text
old blocker: calibrated source grid not yet proven source-positive
new blocker: audit whether the positive source rows are diverse and boundary-useful
```

## Terminal Distribution

Rollout terminal reasons:

```text
collision: 9006
obstacle_completed: 3950
horizon: 2884
safe_stop: 0
```

All successful rollouts ended by obstacle completion:

```text
success terminal_reason obstacle_completed: 3950
```

This preserves the M1268 metric correction: horizon-only rows are not counted as
success.

## Source Diversity

Accepted rows by fault-family pair:

```text
single_wheel_brake_pull->single_wheel_brake_pull: 59
left_right_split_mu->left_right_split_mu: 28
single_wheel_grip_collapse->single_wheel_grip_collapse: 21
halfshaft_torque_loss->halfshaft_torque_loss: 0
```

Accepted rows by speed:

```text
14.0: 41
15.0: 31
16.0: 36
```

Initial interpretation:

```text
source-positive evidence is not a single-row artifact;
halfshaft torque loss remains inactive in this lattice;
accepted rows concentrate around the calibrated viable obstacle window.
```

M1272 must audit source diversity and boundary suitability before actor/history
integration.

## Representative Accepted Rows

High-regret accepted examples:

```text
single_wheel_grip_collapse, speed=16, obstacle_x=15, y=0.0, half_width=0.65:
  best_action_l2=1.5
  min_cross_regret=0.5092
  own margins=0.4604 / 0.4604

left_right_split_mu, speed=16, obstacle_x=15, y=0.0, half_width=0.55:
  best_action_l2=1.5
  min_cross_regret=0.1112
  own margins=0.2320 / 0.2320

single_wheel_grip_collapse, speed=14, obstacle_x=12, y=-0.25, half_width=0.55:
  best_action_l2=0.25
  min_cross_regret=0.1078
  own margins=0.3505 / 0.2296
```

These examples show real action divergence under identical visible source
geometry and different simulator-internal left/right/per-wheel fault branches.

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

The added `viability_calibration` profile only changes source-sampling
scenarios for the no-policy source smoke. It does not add per-wheel fault
metadata, source labels, candidate ids, or outcome labels to the actor
observation.

## Failure Taxonomy

M1271 is not a failure. It resolves the M1268/M1269
`scenario_sampling_failure` for this calibrated source grid.

Remaining audit risks:

```text
source_collapse_risk:
  accepted rows may still concentrate in a small geometry/boundary subset.

boundary_usefulness_risk:
  some accepted rows have large positive margins and may be too easy for later
  wrong-history/driver-like evidence.

inactive_fault_family:
  halfshaft_torque_loss produced no accepted rows in this candidate lattice.
```

## Decision

Do not train.

Do not run PPO.

Do not promote.

Do not integrate into Gym/actor yet.

Admit one result audit:

```text
m1272-paper-route-four-wheel-source-viability-calibration-result-audit
```

M1272 should decide whether these accepted rows are suitable for the next
source step, whether they need boundary filtering, and whether halfshaft torque
loss should be dropped, separately mined, or treated as inactive for this
candidate lattice.
