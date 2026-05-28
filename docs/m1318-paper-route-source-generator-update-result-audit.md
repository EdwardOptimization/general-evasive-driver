# M1318 Paper-Route Source Generator Update Result Audit

## Summary

M1318 audits the M1317 expanded source generator smoke.

Decision:

```text
source_generator_update_result_audit_route_to_inactive_family_repair_design
```

M1317 is a valid source-positive infrastructure result:

```text
accepted_separable_pairs: 128
accepted_fault_family_pairs: 5
result_class: capability_separable_signal
source_positive: true
```

But M1317 should not route directly to corpus export, source-history
materialization, objective tuning, PPO, or promotion. It is still partial
coverage: the smoke target was `160` accepted rows, and three target families
remain inactive.

## Evidence

Primary artifacts:

```text
runs/m1317_source_generator_update_smoke/summary.json
runs/m1317_source_generator_update_smoke/family_source_summary.csv
runs/m1317_source_generator_update_smoke/inactive_fault_families.csv
runs/m1317_source_generator_update_smoke/accepted_template_summary.csv
docs/m1317-paper-route-source-generator-update-smoke.md
```

M1317 guardrails held:

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

## What Improved

M1315/M1273 accepted families:

```text
left_right_split_mu
single_wheel_brake_pull
single_wheel_grip_collapse
```

M1317 accepted families:

```text
halfshaft_torque_loss
left_right_split_mu
single_wheel_brake_pull
single_wheel_grip_collapse
tire_blowout_like
```

This is a real generator improvement. Halfshaft torque loss was inactive in
M1271/M1273 and now has `4` strict accepted rows. Tire-blowout-like proxy is a
new distinct source family and has `21` accepted rows.

Accepted counts:

```text
single_wheel_grip_collapse: 47
single_wheel_brake_pull: 44
tire_blowout_like: 21
left_right_split_mu: 12
halfshaft_torque_loss: 4
```

The mixed action lattice also helped. Accepted best-template counts include
release/counter/power templates, not just hard braking:

```text
left_steer_release: 86
right_steer_release: 86
left_release_counter_power: 8
right_release_counter_power: 8
left_lift_then_throttle: 4
right_lift_then_throttle: 4
```

## What Still Fails

Inactive families:

```text
global_friction_step
load_cg_perturbation
steering_actuator_fault
```

Rejection reasons:

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

The dominant failure mode is not metric plumbing. It is source construction:
these parameter-style families do not create enough different optimal open-loop
actions under the current geometry/action lattice.

## Failure Taxonomy

Primary failure type:

```text
scenario_sampling_failure
```

The generator now has more fault profiles, but the current scenario/action
search is still not shaped for global friction, steering delay, or load/CG
ambiguity.

Secondary failure type:

```text
objective_overfit risk if used now
```

If the partial 128-row corpus were exported directly, the next policy-side
objective would likely overfit active families, especially single-wheel grip and
brake asymmetry, while leaving parameter-style dynamics underrepresented.

## Route Decision

Do not route to PPO.

Do not route to source-history objective tuning.

Do not route directly to expanded corpus materialization.

Do not route directly to corpus export as the main paper-route corpus.

Route to a family-specific source repair design:

```text
m1319-paper-route-inactive-source-family-repair-design
```

The repair design should target:

```text
global friction:
  lower-speed stopping and lateral-authority boundary grids;
  action profiles with early/late braking and steer-brake tradeoffs;
  near-boundary own-branch viable scenarios.

steering actuator:
  shorter obstacle timing where steer lag matters;
  longer sequence prefixes to expose delay;
  action templates with early steering, delayed countersteer, and rate-limited recovery.

load / CG:
  higher yaw/lateral-velocity initial states;
  curvature-tagged scenarios;
  templates that separate understeer/oversteer recovery.

halfshaft:
  keep active but undercovered;
  add more throttle/yaw authority scenarios before treating it as robust.
```

## Claim Limits

Allowed claim:

```text
M1317 expanded the source generator and produced strict source-positive partial
coverage across five source families.
```

Not allowed:

```text
the expanded paper-route source corpus is ready;
source-history self-identification is proven;
policy performance improved;
PPO is admitted;
checkpoint promotion is admitted;
global friction, steering actuator, or load/CG source coverage is solved;
tire blowout physics is high fidelity.
```

## Next Milestone

Admit:

```text
m1319-paper-route-inactive-source-family-repair-design
```

Scope:

```text
design family-specific source-repair grids and action profiles;
keep strict acceptance thresholds;
do not train;
do not run PPO;
do not promote;
do not use private holdout;
do not change actor inputs.
```
