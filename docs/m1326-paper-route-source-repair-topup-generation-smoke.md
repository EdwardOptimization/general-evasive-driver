# M1326 Paper-Route Source Repair Top-Up Generation Smoke

## Summary

M1326 implemented `source_topup_v1` and ran the first no-policy top-up source
generation smoke.

Decision:

```text
source_repair_topup_smoke_invalid_short_horizon_route_to_horizon_corrected_smoke
```

The implementation compiles and the focused profile tests pass, but the smoke
command used `--sequence-length 9`. That was too short for source acceptance:
every rollout terminated by horizon, so no condition had a viable own-branch
success. The result is therefore a configuration artifact, not evidence that
the top-up source families are intrinsically unseparable.

## Focused Tests

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_four_wheel_fault_source_shape.py
```

Result:

```text
14 passed in 0.95s
```

The tests cover:

```text
source_topup_v1 fault profile
source_topup_v1 fault pairs
source_topup_v1 scenario profile
source_topup_v1 action lattice
existing source_expansion_v1 and source_repair_v1 behavior
```

## Smoke Command

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.four_wheel_fault_source_shape \
  --fault-profile source_topup_v1 \
  --scenario-profile source_topup_v1 \
  --action-profile source_topup_v1 \
  --sequence-length 9 \
  --run-dir runs/m1326_source_repair_topup_generation_smoke
```

## Result

Summary:

```text
fault_profile: source_topup_v1
scenario_profile: source_topup_v1
action_profile: source_topup_v1
sequence_length: 9
scenario_count: 56
fault_count: 86
fault_pair_count: 47
matched_pair_count: 2632
action_lattice_rows: 45
action_rollouts: 236880
accepted_separable_pairs: 0
accepted_fault_family_pairs: 0
inactive_fault_family_count: 8
own_branch_viability_fail_count: 2632
terminal_reason_counts: {'horizon': 236880}
result_class: action_divergent_low_regret
source_positive: false
```

All family pairs are inactive in this run:

```text
global_friction_step->global_friction_step: 0 / 280
halfshaft_torque_loss->halfshaft_torque_loss: 0 / 336
left_right_split_mu->left_right_split_mu: 0 / 168
load_cg_perturbation->load_cg_perturbation: 0 / 448
single_wheel_brake_pull->single_wheel_brake_pull: 0 / 448
single_wheel_grip_collapse->single_wheel_grip_collapse: 0 / 336
steering_actuator_fault->steering_actuator_fault: 0 / 280
tire_blowout_like->tire_blowout_like: 0 / 336
```

## Interpretation

The result is invalid for source-family capability claims.

Reason:

```text
sequence_length=9 gives only 0.18 s at dt=0.02.
```

M1320's valid `source_repair_v1` run used the default `sequence_length=72`.
With a 9-step horizon, vehicles do not pass the obstacle and do not stop, so
source acceptance collapses through own-branch viability:

```text
own_branch_viability_fail_count: 2632 / 2632
success_terminal_reason_counts: {}
```

Supported:

```text
source_topup_v1 profile wiring and tests are valid.
```

Falsified:

```text
sequence_length=9 is an admissible source-shape smoke horizon for this task.
```

Not supported:

```text
source_topup_v1 improves source coverage;
source_topup_v1 fails under a valid horizon;
the corpus is ready for materialization;
PPO or promotion is admitted.
```

## Failure Taxonomy

Primary:

```text
metric_artifact
```

The zero-acceptance result is dominated by a too-short source horizon.

Secondary:

```text
scenario_sampling_failure
```

The current top-up scenarios are not meaningful under a 9-step acceptance
horizon.

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
m1327-paper-route-source-repair-topup-horizon-corrected-smoke
```

Scope:

```text
rerun source_topup_v1 with sequence_length=72;
use a new run directory;
do not change accepted thresholds;
do not train;
do not run PPO;
do not promote.
```
