# M1327 Paper-Route Source Repair Top-Up Horizon-Corrected Smoke

## Summary

M1327 reran `source_topup_v1` with the historical source-mining horizon:

```text
sequence_length: 72
```

Decision:

```text
source_topup_horizon_corrected_mixed_route_to_additive_merge_audit
```

The result is source-positive, so M1326's zero-acceptance result is confirmed as
a short-horizon artifact. However, M1327 is not a standalone replacement for
M1322:

```text
M1322 accepted rows: 216
M1327 accepted rows: 150
```

M1327 is best treated as additive top-up evidence. It strongly improves some
undercovered active families, especially load/CG and brake asymmetry, while
halfshaft and global friction remain inactive.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.four_wheel_fault_source_shape \
  --fault-profile source_topup_v1 \
  --scenario-profile source_topup_v1 \
  --action-profile source_topup_v1 \
  --sequence-length 72 \
  --run-dir runs/m1327_source_repair_topup_horizon_corrected_smoke
```

## Result

Summary:

```text
fault_profile: source_topup_v1
scenario_profile: source_topup_v1
action_profile: source_topup_v1
sequence_length: 72
scenario_count: 56
fault_count: 86
fault_pair_count: 47
matched_pair_count: 2632
action_lattice_rows: 45
action_rollouts: 236880
accepted_separable_pairs: 150
accepted_fault_family_pairs: 6
inactive_fault_family_count: 2
result_class: capability_separable_signal
source_positive: true
```

Terminal reasons are now valid for source acceptance:

```text
terminal_reason_counts:
  collision: 221416
  obstacle_completed: 15432
  horizon: 32

success_terminal_reason_counts:
  obstacle_completed: 15432
```

## Family Results

Accepted family counts:

```text
load_cg_perturbation: 48
single_wheel_brake_pull: 52
steering_actuator_fault: 38
tire_blowout_like: 8
left_right_split_mu: 2
single_wheel_grip_collapse: 2
```

Inactive:

```text
global_friction_step: 0 / 280
halfshaft_torque_loss: 0 / 336
```

The top-up profile is therefore useful for:

```text
load/CG enrichment
brake asymmetry enrichment
some steering/top-up diversity
some tire-blowout-like enrichment
```

It is not useful as written for:

```text
halfshaft top-up
global friction source coverage
```

## Comparison To M1322

M1322 family counts:

```text
single_wheel_grip_collapse: 62
steering_actuator_fault: 58
left_right_split_mu: 35
tire_blowout_like: 23
halfshaft_torque_loss: 22
single_wheel_brake_pull: 10
load_cg_perturbation: 6
```

M1327 family counts:

```text
single_wheel_brake_pull: 52
load_cg_perturbation: 48
steering_actuator_fault: 38
tire_blowout_like: 8
left_right_split_mu: 2
single_wheel_grip_collapse: 2
```

Naive additive family counts before dedupe:

```text
single_wheel_grip_collapse: 64
steering_actuator_fault: 96
left_right_split_mu: 37
tire_blowout_like: 31
halfshaft_torque_loss: 22
single_wheel_brake_pull: 62
load_cg_perturbation: 54
```

Naive additive total:

```text
366
```

This is only a planning signal. M1328 must audit merge identity and dedupe before
claiming a merged corpus count.

## Interpretation

Supported:

```text
source_topup_v1 is source-positive under a valid 72-step horizon.
```

Supported:

```text
M1327 provides strong additive top-up candidates for load/CG and brake
asymmetry.
```

Falsified:

```text
source_topup_v1 can directly replace M1322 as a standalone expanded corpus.
```

Still unsupported:

```text
halfshaft top-up is solved;
global friction is solved;
source-history materialization is admitted without a merge audit;
PPO or promotion is admitted.
```

## Failure Taxonomy

Primary:

```text
scenario_sampling_failure
```

The top-up scenario/action grid is source-positive but family-skewed: it
enriches load/CG and brake but loses halfshaft.

Secondary risk:

```text
objective_overfit
```

If used alone, M1327 would overrepresent load/CG, brake, and steering while
underrepresenting the M1322 source families it dropped.

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
m1328-paper-route-source-topup-additive-merge-audit
```

Scope:

```text
audit whether M1322 + M1327 can form an additive merged source corpus;
dedupe by source identity rather than naive counts;
keep global friction and halfshaft blockers explicit;
do not train;
do not run PPO;
do not promote.
```
