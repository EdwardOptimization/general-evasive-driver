# M703 Extreme Dynamics Scenario Corpus Design

## Purpose

M703 designs the next branch after M702:

```text
extreme_hidden_condition_scenario_generation
```

The goal is to produce a no-training scenario corpus that actually stresses
online self-identification. The corpus should contain hidden vehicle/surface
capability changes that are not visible to the actor as labels, but are
inferable through command-response history.

This milestone is design-only:

```text
no implementation
no actor training
no objective update
no PPO
no checkpoint promotion
no actor-input change
```

## Background

M701 showed that the current fresh/ood scenario distribution is not enough:

```text
accepted_rows:                   99
source_positive_variants:         0
history_action_critical_rows:     0
result_class: scale_sparse_plausible
```

The right next question is not:

```text
Can we tune another sampler threshold?
```

The right next question is:

```text
Can we construct hidden-condition evasive scenarios where the same visible
road/obstacle situation requires different actions because the vehicle's
actual capability has changed?
```

## Modeling Boundary

Current AutoDrift uses a single-track RWD model with:

```text
VehicleParams.mu
VehicleParams.cf / cr
VehicleParams.mass / iz / lf / lr
VehicleParams.max_drive_force
VehicleParams.max_brake_force
VehicleParams.max_steer / max_steer_rate
VehicleParams.drive_tau / steer_tau
```

This can honestly represent hidden capability changes at the vehicle or axle
level. It cannot honestly represent true left/right single-wheel asymmetry.

So M704 should be explicit:

```text
current-model fault:
  supported by the single-track dynamics

current-model proxy:
  an honest capability-loss proxy, not claimed as true single-wheel physics

future four-wheel fault:
  deferred until a four-wheel dynamics model or higher-fidelity engine exists
```

This prevents the project from pretending that a bicycle model can simulate a
single-corner blowout or stuck caliper yaw moment.

## Actor Input Contract

Actor inputs remain P0 human-view/no-wheel mainline:

```text
ego kinematics and IMU-like response
steering/throttle/brake actuator state
previous physical commands
road/free-space/obstacle geometry in ego frame
recurrent hidden state from past command-response history
```

Actor inputs must not include:

```text
fault_family
fault_severity
fault_activation_step
mu or hidden vehicle params
oracle feasibility labels
AEB/AES/drift-required labels
controller mode
reference path error or TTC
```

Fault labels are allowed only for:

```text
scenario generation
logging
teacher/oracle analysis
corpus mining
audit stratification
```

## Current-Model Fault Families

M704 should implement current-model-compatible faults first.

### global_mu_drop

Represents:

```text
sudden ice/wet/oil patch
uniform surface friction drop
```

Implementation route:

```text
reuse and generalize existing friction_step
allow activation before obstacle or during warm-up
severity ladder: mild, moderate, severe, extreme
```

### front_lateral_authority_drop

Represents:

```text
front tire lateral capacity/stiffness loss
understeer-heavy emergency fault
front axle grip collapse proxy
```

Implementation route:

```text
scale cf down
optionally reduce front effective capacity if dynamics support per-axle mu
```

### rear_lateral_authority_drop

Represents:

```text
rear tire lateral capacity/stiffness loss
oversteer or drift-recovery challenge
rear axle grip collapse proxy
```

Implementation route:

```text
scale cr down
optionally reduce rear effective capacity if dynamics support per-axle mu
```

### brake_authority_drop

Represents:

```text
brake fade
hydraulic pressure loss
low effective braking force
```

Implementation route:

```text
scale max_brake_force down before or during warm-up
```

### drive_authority_drop

Represents:

```text
drive torque loss
half-shaft / motor failure proxy
```

Implementation route:

```text
scale max_drive_force down
```

Limit:

```text
This is not true left/right half-shaft asymmetry in the current model.
```

### steering_fault

Represents:

```text
steering lag
steering rate limit
partial steering authority loss
deadzone/stiction proxy
```

Implementation route:

```text
increase steer_tau
reduce max_steer_rate
reduce max_steer
optionally add deterministic deadzone in actuator command processing
```

### mass_cg_shift

Represents:

```text
payload change
CG shift
changed yaw inertia
```

Implementation route:

```text
sample mass, iz, lf, lr from a wider hidden-condition ladder
```

This is probably an initial hidden condition rather than a sudden mid-episode
fault.

### delay_noise_fault

Represents:

```text
sensor delay
actuator delay
IMU noise or bias
```

Implementation route:

```text
increase drive_tau / steer_tau
apply observation delay/noise wrappers during scenario generation
```

Observation noise must not reveal a fault label.

### combined_fault

Represents realistic compound degradation:

```text
low mu + brake fade
rear authority drop + steering lag
front authority drop + high speed
CG shift + brake authority loss
```

Implementation route:

```text
sample two moderate faults rather than one extreme fault
```

This matters because the most self-ID-critical cases may come from ambiguous
combinations, not maximum severity single faults.

## Future Four-Wheel Fault Families

These should be documented but not claimed in the current single-track model:

```text
single_wheel_grip_collapse
single_wheel_puncture_or_blowout
left_right_split_mu
stuck_caliper_or_single-wheel brake pull
true asymmetric half-shaft torque loss
wheel-load-transfer-rich tire temperature faults
```

M704 may include these as `future_only` rows in a design table, but must not
generate them as if they were physically faithful.

## Timing Structure

Each scenario should have three phases:

```text
warmup:
  0.5s-2.0s of ordinary driving, mild maneuver, or lane keeping

fault evidence:
  hidden fault active or activated; actor can infer it only through response

emergency:
  obstacle appears or becomes unavoidable by braking-only response
```

Two activation modes are needed:

```text
pre_existing_fault:
  fault active from reset, evidence gathered during warm-up

surprise_fault:
  fault activates during warm-up or just before obstacle reveal
```

Do not start with the emergency at step 0. A self-ID driver needs response
history before the decision point.

## Scenario Geometry

M704 should include:

```text
straight road obstacle
curved road obstacle
lane/corridor narrowing
offset obstacle requiring stable AES
close obstacle requiring drift-like yaw authority
unavoidable collision mitigation case
```

The first implementation can reuse existing obstacle environment geometry, but
the design should name the desired scenario family and obstacle timing.

## Matched Hidden-Condition Corpus

The corpus should not accept rows simply because they are hard. It should
accept rows because hidden vehicle capability changes what action is safe.

For a row to be source-positive, require:

```text
same or matched visible scene geometry
similar current ego state
different hidden fault/capability profile
different action required for margin or success
normal-history rollout succeeds or has positive margin
wrong-history or reset-history rollout has degraded margin or success
```

Snapshot matching features:

```text
vx, vy, yaw_rate
steer actuator state
drive/brake actuator state
obstacle x/y and size
road/free-space local geometry
step or time-to-obstacle window
```

Hidden labels are not matched directly for actor input; they are used to form
pairs and stratify results.

## Source Scoring

Candidate score:

```text
score =
  terminal_margin_gap_between_fault_profiles
  + action_divergence_between_fault_profiles
  + wrong_history_margin_degradation
  + reset_history_margin_degradation
  + fault_family_diversity_bonus
  + near_boundary_margin_bonus
```

Reject:

```text
normal_failed:
  the preferred/normal-history rollout already fails

too_safe:
  all fault histories and ablations succeed with large margin

history_insensitive:
  wrong/reset history does not degrade margin or action choice

unmatched_scene:
  no similar current visible state exists across hidden profiles

model_fidelity_blocked:
  desired fault cannot be represented honestly in current dynamics
```

## Severity Ladder

Each current-model fault should define severity levels:

```text
mild:
  should usually be recoverable and useful for warm-up self-ID

moderate:
  should create different optimal timing or maneuver intensity

severe:
  should force drift-like or aggressive AES behavior in some geometries

extreme:
  may be unavoidable; useful for mitigation but not for source-positive success
```

The corpus should stratify by severity. If all severe/extreme cases are
normal-failed, do not train on them as successful evasive examples; keep them
as mitigation or diagnostic cases.

## Artifacts

M704 should produce a no-training run directory:

```text
runs/m704_extreme_dynamics_scenario_corpus/
```

Required artifacts:

```text
summary.json
scenario_summary.csv
fault_family_summary.csv
severity_summary.csv
snapshot_candidates.csv
matched_hidden_condition_pairs.csv
intervention_rollouts.csv
accepted_rows.csv
rejected_rows.csv
model_fidelity_limits.md
```

Suggested `summary.json` fields:

```text
run_type: extreme_dynamics_scenario_corpus
training_started: false
ppo_used: false
promoted: false
actor_parameters_changed: false
scenario_count
snapshot_count
matched_pair_count
accepted_rows
history_action_critical_rows
source_positive
current_model_fault_families
future_only_fault_families
result_class
```

## Result Classes

M704 should classify:

```text
extreme_source_positive:
  current-model fault corpus yields source-diverse history-action-critical rows

extreme_source_sparse:
  accepted rows exist but not enough diversity or history-critical volume

all_failed_too_severe:
  scenarios are too extreme; preferred history already fails

history_insensitive_too_mild:
  faults do not materially change action or margin

matched_state_empty:
  generated scenarios do not produce comparable visible states across hidden
  profiles

model_fidelity_blocked:
  requested fault families require four-wheel physics before meaningful corpus
  generation

implementation_failed:
  artifacts missing or actor mutated
```

Only `extreme_source_positive` can admit objective/corpus export design.

## Acceptance Thresholds

Initial source-positive thresholds:

```text
accepted_rows >= 80
history_action_critical_rows >= 30
unique_fault_families >= 4
unique_severities >= 2
unique_seeds >= 30
unique_geometry_buckets >= 4
max_fault_family_dominance <= 0.35
max_seed_dominance <= 0.08
normal_history_success_rate >= 0.80 on accepted rows
wrong_or_reset_degradation_rate >= 0.50 on accepted rows
```

These can be adjusted only by a later audit, not after seeing a failed M704
result.

## Smoke Then Full

M704 should support a smoke run:

```text
seed_count: 64
fault_families: global_mu_drop, brake_authority_drop, steering_fault
severity: mild, moderate
```

Full registered run:

```text
seed_count: 512 or 1024
fault_families:
  global_mu_drop
  front_lateral_authority_drop
  rear_lateral_authority_drop
  brake_authority_drop
  drive_authority_drop
  steering_fault
  mass_cg_shift
  delay_noise_fault
  combined_fault
severity: mild, moderate, severe, extreme
geometry: straight, curved, offset obstacle, close obstacle
```

The full run should be no-training and can be CPU-only.

## Implementation Sketch

M704 can add:

```text
src/autodrift/extreme_dynamics_scenario_corpus.py
tests/test_extreme_dynamics_scenario_corpus.py
configs/extreme_hidden_condition_scenarios.json
```

Minimal data structures:

```text
FaultSpec:
  family
  severity
  activation_mode
  activation_step
  warmup_steps
  params
  fidelity_class

ScenarioSpec:
  seed
  geometry
  speed
  obstacle_timing
  fault_spec
```

The environment change should be conservative. Prefer adding a hidden fault
application layer that updates `VehicleParams` at reset or activation time,
without changing observation shape.

## Decision

M703 admits M704 implementation:

```text
extreme_dynamics_scenario_corpus_design_admit_m704
```

Blocked until M704:

```text
source corpus export
objective design
actor update
PPO
checkpoint promotion
four-wheel model migration
```
