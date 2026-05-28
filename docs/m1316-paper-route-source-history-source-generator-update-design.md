# M1316 Paper-Route Source-History Source Generator Update Design

## Summary

M1316 designs the source generator update required by M1315's coverage-gap
report.

Decision:

```text
source_generator_update_design_admit_source_generation_smoke
```

The current source-history substrate should not be materialized as the expanded
paper-route corpus. It covers only:

```text
planned_source_pairs: 108 / 240 target
planned_pair_probe_groups: 216 / 480 target
source_fault_family_count: 3 / 6 target
corner_or_side_variant_count: 3
materialized_source_pair_count: 38
max_source_family_fold_share: 0.5789473684
```

The immediate blocker is not another policy objective. The generator itself
must cover more physical source families and source variants before more
source-history optimization, PPO, or promotion.

No training, PPO, checkpoint promotion, private holdout, actor-input expansion,
threshold relaxation, high-fidelity validation claim, paper-level claim, or
closed-loop self-identification claim occurs in M1316.

## Evidence Base

M1315 reports these source generator gaps:

```text
global_friction_step->global_friction_step: missing
halfshaft_torque_loss->halfshaft_torque_loss: missing
load_cg_perturbation->load_cg_perturbation: missing
steering_actuator_fault->steering_actuator_fault: missing
tire_blowout_like->tire_blowout_like: missing
left_right_split_mu->left_right_split_mu: 28 / 30 under target
single_wheel_grip_collapse->single_wheel_grip_collapse: 21 / 30 under target
```

The current source code already has a compact four-contact-patch model with
per-wheel scale vectors:

```text
mu
lateral_stiffness
brake
drive
```

This is enough for split-mu, brake asymmetry, and some single-wheel grip
collapse, but the current generator is hard-coded to a narrow set of faults,
scenarios, and brake-heavy action templates.

## Design Principle

Do not add fault labels or privileged parameters to the actor.

The source generator may use fault metadata for offline source construction,
fold assignment, and diagnostics. The deployable actor remains:

```text
P0 human-view no-wheel 72-dim frame + online GRU hidden state
```

Allowed actor-view history remains:

- ego kinematics / IMU-like response;
- steering, throttle, and brake actuator state;
- previous physical commands;
- road / free-space / obstacle geometry in ego frame.

Forbidden actor inputs remain:

- fault family or fault label;
- `mu`, per-wheel `mu`, tire force, slip, or friction margin;
- mass, CG, brake scale, tire stiffness, actuator hidden parameters;
- oracle feasibility, source-search output, success label, TTC, path error, or
  controller mode.

## Generator Architecture Update

M1317 should split the current hard-coded generator into three selectable
profiles:

```text
fault_profile
scenario_profile
action_profile
```

The first implementation can keep the old defaults for backward compatibility:

```text
fault_profile=m1268_default
scenario_profile=m1268_default or viability_calibration
action_profile=brake_avoidance_v1
```

Add a new paper-route profile:

```text
fault_profile=source_expansion_v1
scenario_profile=source_expansion_v1
action_profile=mixed_emergency_v1
```

The source expansion profile should emit explicit metadata for:

```text
source_family_pair
condition_A_fault
condition_B_fault
corner_or_side_variant
severity
onset_timing_bin
speed_bin
curvature_bin
scenario_profile
action_profile
```

For M1317, onset timing and curvature may be coarse source tags if the source
rollout still uses a fixed source condition. They must not be accepted as
closed-loop self-identification evidence until later response-history
materialization actually realizes the timing in actor-view histories.

## Source Family Plan

### Split-Mu Road

Current status:

```text
supported but under target
```

Keep the existing left-low/right-low pair and add severity variants:

```text
left_scale/right_scale:
  0.15 / 1.0
  0.25 / 1.0
  0.40 / 1.0
  0.60 / 1.0
```

Use both side directions:

```text
left_low vs right_low
right_low vs left_low
```

Acceptance remains action-divergence based. A split-mu label alone is not a
valid source row.

### Single-Wheel Grip Collapse

Current status:

```text
supported but under target and mostly rear-wheel variants
```

Extend variants to all four corners:

```text
front_left
front_right
rear_left
rear_right
```

Use at least two severities:

```text
mu_scale / lateral_stiffness_scale:
  0.15 / 0.15
  0.25 / 0.25
  0.40 / 0.40
```

Pair same-axle left/right and front/rear alternatives only if both branches have
own-branch viable actions and cross-regret.

### Brake Asymmetry

Current status:

```text
available but overrepresented and margin-easy
```

Keep it, but reduce dominance by generating more balanced variants:

```text
front_left pull vs front_right pull
rear_left pull vs rear_right pull
front_left weak brake vs front_right weak brake
rear_left weak brake vs rear_right weak brake
```

Use severity variants:

```text
stuck/pull brake_scale: 1.5, 2.0, 2.5
weak/lost brake_scale: 0.15, 0.40, 0.65
```

Fold planning should cap this family so it does not dominate every split.

### Halfshaft / Drive Torque Loss

Current status:

```text
currently inactive in M1271/M1273
```

The dynamics already supports per-wheel `drive` scale, but the existing action
lattice is brake dominated. Halfshaft loss cannot be judged fairly until the
action profile contains throttle/yaw-authority maneuvers.

M1317 should add drive-sensitive templates:

```text
left_steer_throttle
right_steer_throttle
left_steer_lift_then_throttle
right_steer_lift_then_throttle
left_power_recovery
right_power_recovery
```

Accept halfshaft rows only if the new lattice creates real action divergence:

```text
best_action_l2 >= 0.12
min(cross_regret_A, cross_regret_B) >= 0.02
best_A_success == true
best_B_success == true
```

If halfshaft remains inactive, M1317 must report it as inactive again rather
than forcing it into the accepted corpus.

### Tire Blowout-Like Event

Current status:

```text
not represented as a distinct family
```

The in-repo model cannot claim true tire blowout physics. M1317 may implement a
bounded `tire_blowout_like` proxy only if the dynamics applies more than a
renamed grip-collapse label.

Minimum proxy:

```text
corner-specific mu reduction
corner-specific lateral stiffness reduction
corner-specific extra rolling/longitudinal drag
```

This requires extending `FourWheelFaultScales` with a per-wheel drag or rolling
loss term and testing that the additional drag creates the expected signed yaw
moment.

Allowed claim:

```text
blowout-like asymmetric response proxy for source mining
```

Blocked claim:

```text
validated tire blowout physics
```

### Global Friction Step

Current status:

```text
missing but representable as uniform per-wheel mu/stiffness scale
```

M1317 can add global conditions with all wheels scaled together:

```text
global_high_mu
global_medium_mu
global_low_mu
global_very_low_mu
```

A global friction pair may be harder to accept because it produces less
left-right yaw asymmetry. It is still useful if it creates different emergency
actions through braking/lateral authority. It must pass the same strict
own-branch and cross-regret gates.

### Steering Actuator Fault

Current status:

```text
missing because source cases cannot override actuator parameters
```

M1317 should allow a `FourWheelFaultCase` to carry optional per-condition
vehicle parameter overrides. Then steering faults can use:

```text
slow_steer_tau
low_max_steer_rate
reduced_max_steer
```

These are hidden simulator parameters and remain forbidden actor inputs.

### Load / CG Perturbation

Current status:

```text
missing because source cases cannot override vehicle parameters
```

Use the same parameter-override mechanism as steering faults:

```text
mass scale
inertia scale
lf/lr shift
h_cg shift
```

This is a compact source-mining proxy. It is not a high-fidelity load-transfer
validation because the current model still uses a simple static load split.

## Scenario Profile Update

The current `viability_calibration` profile was enough for first source-positive
evidence but is too narrow for paper-route source-history work.

Add:

```text
source_expansion_v1
```

Minimum axes:

```text
speed bins: 12, 14, 16, 18, 20 m/s
obstacle distance bins: 10, 12, 14, 16, 18 m
obstacle lateral offsets: -0.45, -0.25, 0.0, 0.25, 0.45
obstacle half-widths: 0.55, 0.65, 0.75, 0.85
initial yaw-rate bins: mild left, zero, mild right
initial lateral velocity bins: mild left, zero, mild right
```

The full Cartesian product may be too large. M1317 can use deterministic
stratified sampling, but it must record the planned axes and generated counts.

## Action Profile Update

Add:

```text
mixed_emergency_v1
```

It should include the current brake-heavy candidates plus:

```text
steer + throttle
steer + throttle release
steer + half brake
steer + brake release
countersteer with delayed brake release
countersteer with delayed throttle recovery
```

The action profile should not add rule-based modes to the actor. It is only an
offline open-loop candidate lattice for finding source pairs with different
correct actions.

## Acceptance Criteria for Source Rows

Keep the strict source acceptance gates unchanged:

```text
best_A_success == true
best_B_success == true
margin_A_best_A >= 0.0
margin_B_best_B >= 0.0
best_action_l2 >= 0.12
cross_regret_A >= 0.02
cross_regret_B >= 0.02
```

Add expansion diagnostics:

```text
accepted_fault_family_pairs >= 5, or report per-family blockers
accepted_separable_pairs >= 160, or report coverage gaps
accepted rows not dominated by one family
accepted rows not dominated by one action template
inactive families exported separately
no all-collision source rows accepted
labels_enter_actor_input == false
training_started == false
ppo_used == false
promoted == false
private_holdout_used == false
actor_input_contract_changed == false
accepted_thresholds_relaxed == false
```

M1317 should not promise the final M1314 target of `240` source pairs. It should
first test whether the generator update creates enough valid family coverage to
route to a new corpus export/materialization branch.

## Blocked Families and Claim Limits

Blocked as high-fidelity claims in this branch:

```text
true tire pressure/radius/thermal blowout
true drivetrain halfshaft transient or differential dynamics
true suspension damage
true wheel-speed sensor failure
validated load-transfer physics
external-simulator or real-vehicle validation
```

These may be future branches, but M1317 should keep the local generator compact
and deterministic.

## Next Milestone

Admit:

```text
m1317-paper-route-source-generator-update-smoke
```

Scope:

```text
implement selectable fault/scenario/action profiles
add focused dynamics/source-shape tests
run one no-policy source-generation smoke
write accepted and inactive family diagnostics
do not train
do not run PPO
do not promote
do not use private holdout
do not change actor inputs
```

The expected next decision is one of:

```text
source_generator_update_smoke_route_to_corpus_export
source_generator_update_smoke_gap_reported_route_to_family_repair
source_generator_update_smoke_blocked_route_to_simulator_extension_design
```

M1317 should decide from actual generated artifacts, not from design intent.
