# M1320 Paper-Route Inactive Source Family Repair Smoke

## Summary

M1320 implemented and ran the no-policy `source_repair_v1` repair smoke admitted
by M1319.

Decision:

```text
inactive_source_family_repair_smoke_strong_partial_route_to_result_audit
```

This is a strong source-generation result:

```text
accepted_separable_pairs: 216
accepted_fault_family_pairs: 7
result_class: capability_separable_signal
source_positive: true
```

M1320 clears the M1320 smoke thresholds for accepted rows and accepted family
count. It also activates two of the three M1317 inactive families:

```text
steering_actuator_fault: 58 accepted rows
load_cg_perturbation: 6 accepted rows
```

Halfshaft coverage improves from `4` to `22` accepted rows.

The remaining blocker is global friction:

```text
global_friction_step: 0 accepted rows
```

Do not run PPO or promote. The next step is a result audit to decide whether to
export the seven-family source corpus or first isolate global-friction repair.

## Commands

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_four_wheel_fault_source_shape.py tests/test_four_wheel_dynamics.py
```

Result:

```text
17 passed in 2.09s
```

Repair smoke:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.four_wheel_fault_source_shape \
  --fault-profile source_repair_v1 \
  --scenario-profile source_repair_v1 \
  --action-profile source_repair_v1 \
  --run-dir runs/m1320_inactive_source_family_repair_smoke
```

## Implementation

M1320 added:

- `source_repair_v1` fault profile;
- `source_repair_v1` scenario profile;
- `source_repair_v1` action profile;
- multi-phase action templates in the source lattice;
- drive/coast/mixed preloaded source scenarios;
- stronger parameter repair pairs for global friction, steering actuator,
  load/CG, and halfshaft.

This remains source-only offline machinery. The deployable actor action and
observation contracts are unchanged.

## Result

Summary:

```text
scenario_count: 60
fault_count: 56
fault_pair_count: 32
matched_pair_count: 1920
action_lattice_rows: 37
action_rollouts: 142080
accepted_separable_pairs: 216
rejected_pairs: 1704
best_actions_diverged_pairs: 1029
low_regret_pairs: 1297
own_branch_viability_fail_count: 985
accepted_fault_family_pairs: 7
inactive_fault_family_count: 1
result_class: capability_separable_signal
source_positive: true
```

Accepted families:

```text
single_wheel_grip_collapse: 62
steering_actuator_fault: 58
left_right_split_mu: 35
tire_blowout_like: 23
halfshaft_torque_loss: 22
single_wheel_brake_pull: 10
load_cg_perturbation: 6
```

Inactive family:

```text
global_friction_step: 0
```

## Compared With M1317

M1317:

```text
accepted_separable_pairs: 128
accepted_fault_family_pairs: 5
inactive_fault_family_count: 3
halfshaft accepted rows: 4
steering accepted rows: 0
load/CG accepted rows: 0
```

M1320:

```text
accepted_separable_pairs: 216
accepted_fault_family_pairs: 7
inactive_fault_family_count: 1
halfshaft accepted rows: 22
steering accepted rows: 58
load/CG accepted rows: 6
```

This supports the M1319 diagnosis: the previous inactive families were mostly a
scenario/action-search problem, not a fundamental failure of the source
framework.

## Remaining Global-Friction Blocker

Global friction summary:

```text
matched_pairs: 300
accepted_pairs: 0
rejected_pairs: 300
best_actions_too_close: 119
best_candidate_not_viable: 181
```

Interpretation:

Uniform global friction variation is still not generating strict action
separability under this open-loop source formulation. This may require a
different source construction style:

- capability-envelope source labels rather than symmetric paired actions;
- longer stopping-distance corridor tasks;
- dynamic friction onset histories;
- separate global-friction source miner;
- or simulator/model changes.

Do not hide this by merging global friction into split-mu or tire-blowout-like
labels.

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

The result is source-generation evidence only. It is not policy performance and
not self-identification proof.

## Decision

M1320 passes as infrastructure. It meets the source-repair smoke acceptance
criteria:

```text
accepted_separable_pairs >= 160
accepted_fault_family_pairs >= 6
at least one previously inactive family becomes active
halfshaft accepted rows > 4
inactive families exported separately
strict source thresholds preserved
```

Admit one result audit:

```text
m1321-paper-route-source-repair-result-audit
```

The audit should decide whether the next route is:

```text
updated seven-family source corpus export;
global-friction-specific source miner design;
or combined export plus separately tracked global-friction blocker.
```
