# M1319 Paper-Route Inactive Source Family Repair Design

## Summary

M1319 designs the next no-policy repair step after M1318 audited M1317 as
source-positive but partial.

Decision:

```text
inactive_source_family_repair_design_admit_no_policy_repair_smoke
```

The next step should not tune a policy or export the partial M1317 corpus as the
main paper-route corpus. It should first repair source generation for families
that are inactive or too thin:

```text
global_friction_step: inactive
steering_actuator_fault: inactive
load_cg_perturbation: inactive
halfshaft_torque_loss: active but only 4 accepted rows
```

No training, PPO, checkpoint promotion, private holdout, actor-input expansion,
source-threshold relaxation, paper-level claim, high-fidelity claim, or
closed-loop self-identification claim occurs in M1319.

## Why M1317 Needs Repair Before Export

M1317 improved source diversity:

```text
accepted_separable_pairs: 128
accepted_fault_family_pairs: 5
```

But it remains below the M1317 smoke target:

```text
accepted_separable_pairs target: 160
inactive_fault_family_count: 3
```

Direct corpus export now would overrepresent left/right asymmetric local fault
families:

```text
single_wheel_grip_collapse: 47
single_wheel_brake_pull: 44
tire_blowout_like: 21
left_right_split_mu: 12
halfshaft_torque_loss: 4
```

This would likely create another policy-side objective that performs well on
the active public rows while leaving global envelope, steering-delay, and
load/CG response ambiguity underrepresented.

## Repair Strategy

M1320 should add one new no-policy profile:

```text
fault_profile=source_repair_v1
scenario_profile=source_repair_v1
action_profile=source_repair_v1
```

The repair profile should be family-aware in source generation, but not in actor
input. Family labels remain offline metadata only.

Required outputs:

```text
runs/m1320_inactive_source_family_repair_smoke/summary.json
runs/m1320_inactive_source_family_repair_smoke/family_source_summary.csv
runs/m1320_inactive_source_family_repair_smoke/inactive_fault_families.csv
runs/m1320_inactive_source_family_repair_smoke/accepted_template_summary.csv
```

## Global Friction Repair

M1317 failure:

```text
best_actions_too_close: 62
best_candidate_not_viable: 46
accepted: 0
```

Diagnosis:

Uniform friction changes do not create left/right yaw asymmetry. The generator
must expose braking/lateral envelope tradeoffs rather than expecting symmetric
mu changes to behave like split-mu faults.

Repair grid:

```text
mu pairs:
  0.20 vs 0.45
  0.25 vs 0.65
  0.35 vs 0.85

speed bins:
  10, 12, 14, 16, 18 m/s

obstacle distance:
  9, 11, 13, 15, 17 m

obstacle lateral offset:
  -0.25, 0.0, 0.25

obstacle width:
  0.45, 0.60, 0.75
```

Repair action templates:

```text
early_hard_brake
late_hard_brake
early_brake_then_release
left_steer_light_brake
right_steer_light_brake
left_steer_no_brake
right_steer_no_brake
brake_then_left_swerve
brake_then_right_swerve
```

Acceptance remains strict. If global friction still fails, record it as
action-equivalent or simulator/search-blocked rather than accepting weak rows.

## Steering Actuator Repair

M1317 failure:

```text
best_actions_too_close: 98
best_candidate_not_viable: 9
insufficient_cross_regret: 1
accepted: 0
```

Diagnosis:

Steering delay/rate faults are transient. The current two-phase templates do
not make early steering, delayed steering, and countersteer timing different
enough.

Repair changes:

```text
allow multi-phase action templates, not only one or two constant segments;
add early steering pulses;
add delayed steering pulses;
add pulse-then-countersteer;
add hold-then-release templates;
use shorter obstacle timing where steering delay matters.
```

Repair action templates:

```text
early_left_pulse
early_right_pulse
delayed_left_pulse
delayed_right_pulse
left_pulse_counter
right_pulse_counter
left_hold_release
right_hold_release
```

Scenario grid:

```text
speed: 14, 16, 18, 20 m/s
obstacle distance: 8, 10, 12, 14 m
obstacle offset: -0.35, 0.0, 0.35
obstacle width: 0.55, 0.75
initial yaw_rate: -0.05, 0.0, 0.05
```

The implementation may extend `build_action_lattice` to support a list of
phase fractions. This is source-search machinery only and does not change the
deployable actor action contract.

## Load / CG Repair

M1317 failure:

```text
best_actions_too_close: 96
best_candidate_not_viable: 6
insufficient_cross_regret: 6
accepted: 0
```

Diagnosis:

Mass/inertia/CG changes are response-envelope changes, not discrete left/right
force faults. They need entry states where yaw inertia, front/rear balance, and
recovery behavior matter.

Repair grid:

```text
initial yaw_rate:
  -0.15, -0.08, 0.0, 0.08, 0.15 rad/s

initial lateral velocity:
  -1.0, -0.5, 0.0, 0.5, 1.0 m/s

speed:
  14, 16, 18, 20 m/s

obstacle distance:
  10, 12, 14, 16 m
```

Repair action templates:

```text
countersteer_brake
countersteer_release
steady_steer_brake
steer_then_counter
brake_then_counter
throttle_recovery_counter
```

Load/CG repair must remain honest: the current four-wheel model has only simple
static load split. This can support a compact source-mining proxy, not a
validated load-transfer claim.

## Halfshaft Undercoverage Repair

M1317 result:

```text
accepted: 4
```

Diagnosis:

Halfshaft became active only after adding drive-sensitive action templates.
Coverage remains thin because most source scenarios start in a brake-preloaded
state with `brake_force=6000` and `drive_force=0`.

Repair scenario initializers:

```text
drive_preload:
  drive_force: 2500 to 5000
  brake_force: 0
  previous_action: steer + throttle

coast_preload:
  drive_force: 0
  brake_force: 0
  previous_action: steer + release

mixed_recovery:
  drive_force: 2500
  brake_force: 1500
  previous_action: countersteer + throttle recovery
```

Repair action templates:

```text
left_power_hold
right_power_hold
left_power_then_lift
right_power_then_lift
left_lift_then_power
right_lift_then_power
counter_power_recovery
```

## M1320 Acceptance Criteria

M1320 should pass as infrastructure if:

```text
focused tests pass
runs/m1320_inactive_source_family_repair_smoke/summary.json exists
accepted_separable_pairs >= 160 OR explicit family blockers are reported
accepted_fault_family_pairs >= 6 OR explicit family blockers are reported
at least one previously inactive family becomes active OR all inactive families are classified as simulator/search-blocked
halfshaft accepted rows > 4 OR halfshaft undercoverage blocker is reported
inactive families are exported separately
strict source acceptance thresholds are preserved
labels_enter_actor_input == false
training_started == false
ppo_used == false
promoted == false
private_holdout_used == false
actor_input_contract_changed == false
accepted_thresholds_relaxed == false
```

If the repair smoke improves active-family coverage but still cannot activate
global friction, steering, or load/CG, it should not hide that result. Route to a
simulator/source-search extension audit.

## Implementation Notes

Expected code changes:

```text
src/autodrift/four_wheel_fault_source_shape.py
tests/test_four_wheel_fault_source_shape.py
```

Possible dynamics changes:

```text
none required unless repair needs a stronger explicit actuator fault or load/CG proxy
```

Forbidden:

```text
actor input changes
source threshold relaxation
training
PPO
checkpoint promotion
private holdout use
```

## Next Milestone

Admit:

```text
m1320-paper-route-inactive-source-family-repair-smoke
```

Scope:

```text
implement source_repair_v1 profiles;
run one no-policy repair smoke;
write result doc and diagnostics;
do not train;
do not run PPO;
do not promote.
```
