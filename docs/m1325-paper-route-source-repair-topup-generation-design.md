# M1325 Paper-Route Source Repair Top-Up Generation Design

## Summary

M1325 designs one bounded no-policy top-up source-generation pass after M1324
closed the source-history corpus expansion branch.

Decision:

```text
source_repair_topup_generation_design_admit_no_policy_smoke
```

The next milestone should implement a new source-mining profile:

```text
fault_profile=source_topup_v1
scenario_profile=source_topup_v1
action_profile=source_topup_v1
```

This is source-data construction only. It does not train a driver, run PPO,
promote a checkpoint, use private holdout, change actor inputs, or claim
closed-loop self-identification.

## Target Gaps

M1323 improved the expansion plan substantially but remains under target:

```text
planned_source_pairs: 216 / 240
planned_pair_probe_groups: 432 / 480
source_fault_family_count: 7
max_source_family_fold_share: 0.3260869565
```

Families needing top-up:

```text
halfshaft_torque_loss: 22 / 30
load_cg_perturbation: 6 / 30
single_wheel_brake_pull: 10 / 30
tire_blowout_like: 23 / 30
```

Separate blocker:

```text
global_friction_step: 0 / 30
```

The top-up pass should try to reach the global `240` source-pair target while
keeping global friction explicit. Do not relabel split-mu, tire-blowout-like, or
other asymmetric faults as global friction.

## Source Profile

Add `source_topup_v1` as a new profile rather than mutating
`source_repair_v1`. This keeps M1320/M1322/M1323 reproducible.

Required code scope:

```text
src/autodrift/four_wheel_fault_source_shape.py
tests/test_four_wheel_fault_source_shape.py
```

The CLI choices should admit:

```text
--fault-profile source_topup_v1
--scenario-profile source_topup_v1
--action-profile source_topup_v1
```

M1326 should still use the same strict source acceptance thresholds in the
source miner. No accepted threshold should be relaxed to hit row counts.

## Family-Specific Design

### Halfshaft Torque Loss

Current coverage:

```text
22 / 30
```

Top-up intent:

```text
increase drive-sensitive separability under throttle/yaw authority demands
```

Fault cases:

```text
rear_left_halfshaft_loss_0p05
rear_right_halfshaft_loss_0p05
rear_left_halfshaft_loss_0p20
rear_right_halfshaft_loss_0p20
rear_left_halfshaft_loss_0p50
rear_right_halfshaft_loss_0p50
```

Pairs:

```text
left/right same-severity halfshaft pairs
0p0 vs 0p50 same-side diagnostic pairs only if needed for envelope sensitivity
```

Scenarios:

```text
drive_preload:
  speed: 15, 17, 19 m/s
  obstacle_x: 11, 13, 15 m
  obstacle_y: -0.45, 0.45
  drive_force: 3000, 4500
  brake_force: 0

mixed_recovery:
  speed: 16, 18, 20 m/s
  obstacle_x: 10, 12, 14 m
  yaw_rate: -0.10, 0.10
  lateral_velocity: -0.6, 0.6
  drive_force: 2500
  brake_force: 1200
```

Action templates:

```text
left_power_hold
right_power_hold
left_power_then_lift
right_power_then_lift
left_lift_then_power
right_lift_then_power
counter_power_recovery_left
counter_power_recovery_right
```

### Load / CG Perturbation

Current coverage:

```text
6 / 30
```

Top-up intent:

```text
expose yaw inertia, front/rear balance, and recovery differences after a
nonzero yaw/lateral response has developed
```

Fault cases:

```text
ultra_heavy_high_inertia
ultra_light_low_inertia
front_cg_extreme
rear_cg_extreme
high_yaw_inertia_same_mass
low_yaw_inertia_same_mass
front_bias_high_inertia
rear_bias_low_inertia
```

Pairs:

```text
heavy/light
front/rear CG
high/low yaw inertia
front-bias/high-inertia vs rear-bias/low-inertia
```

Scenarios:

```text
yaw_recovery:
  speed: 16, 18, 20, 22 m/s
  obstacle_x: 10, 12, 14 m
  yaw_rate: -0.18, -0.10, 0.10, 0.18
  lateral_velocity: -1.2, -0.7, 0.7, 1.2
  brake_force: 1500, 3000

curved_entry:
  speed: 16, 18, 20 m/s
  obstacle_y: -0.35, 0.35
  previous_action: countersteer plus release or light brake
```

Action templates:

```text
countersteer_brake_left/right
countersteer_release_left/right
steer_then_counter_left/right
brake_then_counter_left/right
release_then_counter_left/right
```

The claim remains a source-mining proxy. This is not validated load-transfer or
high-fidelity CG dynamics.

### Single-Wheel Brake Pull

Current coverage:

```text
10 / 30
```

Top-up intent:

```text
create brake-authority asymmetry rows that are not dominated by the already
large grip-collapse family
```

Fault cases:

```text
front_left_brake_stuck_3p0
front_right_brake_stuck_3p0
rear_left_brake_stuck_3p0
rear_right_brake_stuck_3p0
front_left_brake_loss_0p0
front_right_brake_loss_0p0
rear_left_brake_loss_0p0
rear_right_brake_loss_0p0
```

Pairs:

```text
left/right stuck high-brake pairs
left/right brake-loss pairs
front/rear same-side diagnostic pairs only for source diagnostics
```

Scenarios:

```text
brake_transition:
  speed: 14, 16, 18, 20 m/s
  obstacle_x: 9, 11, 13 m
  obstacle_y: -0.25, 0.25
  brake_force: 1000, 3000, 5500
```

Action templates:

```text
early_hard_brake
late_hard_brake
early_brake_then_release
left_steer_light_brake
right_steer_light_brake
brake_then_left_swerve
brake_then_right_swerve
release_then_left_swerve
release_then_right_swerve
```

### Tire Blowout-Like Proxy

Current coverage:

```text
23 / 30
```

Top-up intent:

```text
add a few stricter asymmetric drag/friction/radius-like proxy rows while keeping
the claim explicitly proxy-only
```

Fault cases:

```text
front_left_tire_blowout_like_drag_3200
front_right_tire_blowout_like_drag_3200
rear_left_tire_blowout_like_drag_3200
rear_right_tire_blowout_like_drag_3200
front_left_tire_blowout_like_drag_3800
front_right_tire_blowout_like_drag_3800
rear_left_tire_blowout_like_drag_3800
rear_right_tire_blowout_like_drag_3800
```

Pairs:

```text
front-left/front-right same-severity pairs
rear-left/rear-right same-severity pairs
front/rear diagnostic pairs only if source family balance needs them
```

Scenarios:

```text
asymmetric_drag_entry:
  speed: 16, 18, 20 m/s
  obstacle_x: 10, 12, 14 m
  obstacle_y: -0.45, 0.45
  yaw_rate: -0.06, 0.06
  brake_force: 0, 1500, 3000
```

Action templates:

```text
lift_then_counter
counter_then_power
release_counter_power
brake_then_counter
steer_release
```

## Global Friction Diagnostic Path

Global friction should not block the top-up pass forever, but it must remain
visible.

M1326 may include a diagnostic-only global-friction route:

```text
global_friction_envelope_diagnostic_v1
```

This diagnostic can search:

```text
low-mu stopping envelope rows
lateral authority rows
early-vs-late brake timing rows
brake-vs-swerve envelope rows
```

But accepted rows from this diagnostic should be reported separately unless the
same strict separability criteria are met. If uniform friction remains
action-equivalent under same-family pair mining, the result should say:

```text
global_friction_source_miner_mismatch
```

That would route to a later envelope-specific source miner, not threshold
relaxation.

## M1326 Command

M1326 should implement the new profile and run one no-policy smoke:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_four_wheel_fault_source_shape.py

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.four_wheel_fault_source_shape \
  --fault-profile source_topup_v1 \
  --scenario-profile source_topup_v1 \
  --action-profile source_topup_v1 \
  --sequence-length 9 \
  --max-rollouts 180000 \
  --run-dir runs/m1326_source_repair_topup_generation_smoke
```

`--max-rollouts` can be adjusted only downward if runtime is too high; it must
not be used to silently drop difficult families.

## M1326 Acceptance

M1326 should pass as infrastructure if all guardrails hold and one of these
result classes is produced:

```text
topup_source_target_met
topup_source_positive_gap_reported
```

Preferred target:

```text
accepted_separable_pairs >= 240
accepted_fault_family_pairs >= 7
at least two undercovered active families reach 30 accepted rows
no active family regresses in exported source count relative to M1323
global friction blocker is reported separately
```

Admissible gap result:

```text
accepted_separable_pairs > 216
at least two undercovered active families improve
strict thresholds preserved
global friction reported as missing, diagnostic-only, or miner-mismatch
```

Failure:

```text
accepted_separable_pairs <= 216 without a clear blocker
only already-dominant families improve
global friction is hidden or mislabeled
strict thresholds are relaxed
actor inputs change
training, PPO, private holdout, or promotion occurs
```

## Guardrails

M1325 changes no policy behavior:

```text
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
accepted_thresholds_relaxed: false
high_fidelity_validation_claimed: false
```

Allowed claim:

```text
M1325 defines a bounded top-up source-generation design.
```

Not allowed:

```text
driver performance improved;
source-history self-identification is proven;
the corpus is ready for PPO;
global friction is solved;
tire blowout or load/CG physics are high fidelity.
```

## Next Milestone

Admit:

```text
m1326-paper-route-source-repair-topup-generation-smoke
```

Scope:

```text
implement source_topup_v1 profiles;
run focused source-shape tests;
run one no-policy top-up generation smoke;
write result artifacts and diagnostics;
do not train;
do not run PPO;
do not promote.
```
