# M1317 Paper-Route Source Generator Update Smoke

## Summary

M1317 implemented the expanded no-policy source generator profiles designed in
M1316 and ran one source-generation smoke.

Decision:

```text
source_generator_update_smoke_partial_coverage_route_to_result_audit
```

The update is source-positive and expands coverage from `3` accepted families to
`5`, including newly active halfshaft and tire-blowout-like proxy families.
However it does not yet meet the expanded coverage target because accepted rows
remain below the M1317 smoke threshold and three families are still inactive.

Do not route directly to corpus export, source-history materialization, PPO, or
promotion. The next step is a result audit that decides whether to repair
inactive families or export a partial source corpus.

## Commands

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_four_wheel_fault_source_shape.py tests/test_four_wheel_dynamics.py
```

Result:

```text
14 passed in 2.11s
```

Source-generation smoke:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.four_wheel_fault_source_shape \
  --fault-profile source_expansion_v1 \
  --scenario-profile source_expansion_v1 \
  --action-profile mixed_emergency_v1 \
  --run-dir runs/m1317_source_generator_update_smoke
```

## Implementation

M1317 added selectable source profiles:

```text
fault_profile:
  m1268_default
  source_expansion_v1

scenario_profile:
  m1268_default
  viability_calibration
  source_expansion_v1

action_profile:
  brake_avoidance_v1
  mixed_emergency_v1
```

The source expansion includes:

- more split-mu severities;
- all-corner single-wheel grip collapse variants;
- stronger and weak-brake asymmetry variants;
- halfshaft torque-loss variants with drive-sensitive action templates;
- tire-blowout-like proxy variants using per-wheel grip loss plus added drag;
- global friction, steering actuator, and load/CG parameter variants;
- source metadata for family, corner/side variant, severity, timing, and
  curvature bins.

The deployable actor input contract is unchanged. Fault metadata and generator
labels stay in offline source artifacts only.

## Result

Summary:

```text
fault_profile: source_expansion_v1
scenario_profile: source_expansion_v1
action_profile: mixed_emergency_v1
scenario_count: 54
fault_count: 44
fault_pair_count: 23
matched_pair_count: 1242
action_lattice_rows: 21
action_rollouts: 52164
accepted_separable_pairs: 128
rejected_pairs: 1114
best_actions_diverged_pairs: 559
low_regret_pairs: 856
own_branch_viability_fail_count: 494
accepted_fault_family_pairs: 5
inactive_fault_family_count: 3
result_class: capability_separable_signal
source_positive: true
```

Accepted families:

```text
single_wheel_grip_collapse->single_wheel_grip_collapse: 47
single_wheel_brake_pull->single_wheel_brake_pull: 44
tire_blowout_like->tire_blowout_like: 21
left_right_split_mu->left_right_split_mu: 12
halfshaft_torque_loss->halfshaft_torque_loss: 4
```

Inactive families:

```text
global_friction_step->global_friction_step
load_cg_perturbation->load_cg_perturbation
steering_actuator_fault->steering_actuator_fault
```

This is a meaningful improvement over M1273/M1315 because halfshaft is no
longer inactive and a distinct tire-blowout-like proxy family now passes strict
source acceptance. It is not enough for the expanded paper-route source-history
corpus.

## Family Diagnostics

Inactive-family reasons:

```text
global_friction_step:
  best_actions_too_close: 62
  best_candidate_not_viable: 46

load_cg_perturbation:
  best_actions_too_close: 96
  best_candidate_not_viable: 6
  insufficient_cross_regret: 6

steering_actuator_fault:
  best_actions_too_close: 98
  best_candidate_not_viable: 9
  insufficient_cross_regret: 1
```

Interpretation:

- global friction needs different geometry and perhaps a braking/lateral
  envelope-oriented source search, not just uniform scale pairs on the current
  grid;
- load/CG perturbation mostly produces action-equivalent rows under the current
  open-loop lattice;
- steering actuator faults mostly produce action-equivalent rows because the
  sequence lattice and rollout horizon do not sufficiently expose delay/rate
  differences.

## Action Template Diagnostics

The accepted rows are not only brake-only rows. Accepted best-template counts
include:

```text
left_steer_release: 86
right_steer_release: 86
left_steer_brake: 12
right_steer_brake: 12
counter_left: 8
counter_right: 8
left_release_counter_power: 8
right_release_counter_power: 8
left_lift_then_throttle: 4
right_lift_then_throttle: 4
```

The drive-sensitive additions are useful but still sparse. Halfshaft accepted
only `4` rows, so it should be treated as newly active but undercovered.

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

The tire-blowout family is explicitly a blowout-like source proxy, not a
validated tire blowout model.

## Decision

M1317 passes as infrastructure because:

- focused tests pass;
- strict acceptance thresholds are preserved;
- accepted and inactive family diagnostics are exported;
- no fake labels are accepted;
- no training, PPO, promotion, private holdout, threshold relaxation, or
  actor-input expansion occurred.

M1317 does not meet the stronger coverage target:

```text
accepted_separable_pairs: 128 < 160 smoke target
accepted_fault_family_pairs: 5, meets family smoke target
inactive_fault_family_count: 3
```

Admit one result audit:

```text
m1318-paper-route-source-generator-update-result-audit
```

The audit should decide whether the next source step is:

```text
family-specific repair for global/steering/load families
partial corpus export with five active families
simulator/source-search extension for parameter-style faults
```

PPO and promotion remain blocked.
