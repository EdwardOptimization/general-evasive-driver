# M91 Input Observability Audit Protocol

This protocol supersedes the immediate M90 PPO continuation. M90 remains useful
as a later guarded continuation, but the current research risk is input
cleanliness and observability: before training another driver, prove which
deployable signals contain the information needed for online self-identification.

## Goal

Answer three questions before the next serious RL comparison:

```text
1. Is the hidden handling envelope observable from the minimum sensor set?
2. Is wheel speed / wheel response necessary beyond body response?
3. Do optional sensors justify their complexity, or only add shortcuts?
```

The target claim is not "the policy predicts mu." The target claim is:

```text
history of commands + sensed vehicle response lets the driver infer
what maneuvers are currently feasible.
```

## Locked Comparison Rule

Do not compare input profiles while tuning PPO independently for each profile.

The required order is:

```text
1. Run cheap supervised probes to test observability.
2. Use P0/P1 pilot RL only to find a stable recipe.
3. Freeze the recipe.
4. Train all compared profiles with the same recipe, seeds, reward, curriculum,
   evaluation corpus, and promotion gates.
5. Continue iterating only the best primary profile; keep P0/P1 as regression
   baselines.
```

Any profile comparison that changes reward, curriculum, seed corpus, PPO budget,
auxiliary loss weights, or warm-start policy is not a valid input comparison.

## Core Profiles

The first formal audit compares these profiles:

```text
P0: no-wheel minimal
commands + actuator actuals + IMU + fused speed + scene

P1: minimum set
commands + actuator actuals + wheel speed + IMU + fused speed + scene

P2: P1 + steering torque / EPS current
P3: P1 + roll/pitch/vertical acceleration
P4: P1 + suspension travel
P5: P1 + all optional current sensors
```

Current-code M91-A starts with a smoke approximation over the existing
85-value wheel frame:

```text
p0_no_wheel_response_context = observation[0:12] + observation[25:85]
p1_wheel_response_context    = observation[0:85]
p0_response_only             = observation[0:12]
p1_response_only             = observation[0:25]
wheel_only                   = observation[12:25]
context_only                 = observation[25:85]
```

This is not the final clean sensor contract. The current 13 wheel channels are
front/rear proxy signals, not independent wheel dynamics. The smoke is used to
validate the audit harness and establish a baseline.

## Not Actor Input

These must not enter deployable actor observations:

```text
mu
true tire force
true tire saturation
friction circle margin
oracle AEB/AES/drift feasibility
TTC
required clearance
path lateral error
path heading error
path curvature
speed_ref
beta_target
```

For the final clean profile, also avoid giving advanced derived tire/controller
flags as actor input until they pass the optional-sensor standard:

```text
slip ratio / slip proxy
ABS/TCS/ESC proxy flags
per-wheel brake pressure split
road-surface embedding
sensor confidence / covariance
```

Those values may still be used for offline targets, probes, teachers,
diagnostics, corpus mining, or safety verifiers.

## Experiment A: Information Observability Probe

This is the first and cheapest experiment. It does not train RL.

For each profile and history window:

```text
0.0 s
0.2 s
0.5 s
1.0 s
2.0 s
```

train lightweight supervised probes to predict future handling-envelope targets.

Do not use `mu` as the main target. Preferred targets are:

```text
future_braking_deceleration
future_yaw_response
future_lateral_accel_response
brake_authority_bucket
yaw_authority_bucket
stable_AES_feasibility
drift_AES_feasibility
drift_recoverability
```

M91-A smoke uses standardized short-horizon probes from sampled states:

```text
full brake pulse -> future_braking_deceleration
steering pulse   -> future_yaw_response
steering pulse   -> future_lateral_accel_response
```

Pass evidence:

```text
P1 improves over P0 on held-out episodes.
0.5 s - 1.0 s history improves over current-frame only.
Wheel profiles improve earlier and more consistently than no-wheel profiles.
```

## Experiment B: Minimum-Set Sensor Ablation

Starting from P1:

```text
P1_full:
commands + actuator actuals + wheel speed + IMU + fused speed

P1_no_commands:
actuator actuals + wheel speed + IMU + fused speed

P1_no_actuator_actuals:
commands + wheel speed + IMU + fused speed

P1_no_wheel:
commands + actuator actuals + IMU + fused speed

P1_no_IMU:
commands + actuator actuals + wheel speed + fused speed

P1_no_fused_speed:
commands + actuator actuals + wheel speed + IMU
```

Each ablation runs probes first, then RL only if the probe shows meaningful
information loss.

## Experiment C: RL Profile Comparison

After a stable recipe is found and frozen, train:

```text
pi0: no-wheel minimal
pi1: minimum set
pi2: minimum + steering torque
pi3: minimum + roll/pitch/vertical acceleration
pi4: minimum + suspension
pi5: minimum + all current optional
```

All policies must use the same:

```text
network family
PPO budget
reward
curriculum
training seeds
evaluation corpus
auxiliary losses
warm-start rule
```

The network split remains:

```text
response/self-ID branch:
  commands + actuator actuals + wheel speed + IMU + optional sensors -> GRU

context branch:
  road + obstacle geometry -> feedforward context encoder

fusion:
  response latent + context latent -> action head
```

Wheel and IMU channels must not be placed in the scene context branch.

## Experiment D: Matched Hidden-Dynamics Counterfactual

This is the strongest self-ID evidence.

Construct matched pairs with:

```text
same road geometry
same obstacle geometry
same initial speed
similar current body state
different hidden dynamics
```

Examples:

```text
high mu + normal actuator
low mu + slow steering actuator
normal mu + weak brake
same mu + different tire stiffness
```

Evaluate:

```text
normal history
reset history
wrong history from paired hidden dynamics
delayed history
```

Pass evidence:

```text
wrong high-grip history in low-grip episode -> over-aggressive action, lower margin
wrong low-grip history in high-grip episode -> over-conservative action, lower margin
wrong slow-actuator history -> steering timing or amplitude error
```

If wrong-history does not change behavior, the policy may still be robust, but
it has not proven causal use of action-response history.

## Experiment E: Optional Sensor Admission

An optional sensor enters the final actor only if it satisfies all of:

```text
1. Probe accuracy improves.
2. Held-out hidden-dynamics success or margin improves.
3. Wrong-history counterfactual gap becomes clearer.
4. Noise, delay, and calibration error do not destroy the benefit.
5. The signal is a sensor or low-level actuator measurement, not a high-level
   oracle estimate.
```

Candidate order:

```text
steering torque / EPS current
roll / pitch / vertical acceleration
suspension travel
```

Do not add suspension signals unless the simulator has meaningful suspension or
load-transfer dynamics. Otherwise the feature is likely to become a spurious
correlation.

## Artifact Requirements

Every formal comparison must preserve:

```text
manifest.json
run_receipt.json
config snapshot
git commit and dirty status
training curves when RL is used
probe_summary.csv
policy_summary.csv when RL is used
episodes.csv when RL is used
seed_delta_summary.csv
counterfactual_summary.csv for Experiment D
checkpoint paths
docs/mXX-*.md result note
```

Negative results are required artifacts. They are part of the evidence chain.

## Immediate Route

```text
M91-A: implement and smoke-test the supervised input observability harness.
M91-B: run the formal P0/P1 probe comparison on the legacy proxy wheel profile.
M91-C: implement and smoke-test a cleaner raw wheel-state minimum profile.
M91-D: run the formal P0/P1 probe comparison on the clean raw wheel profile.
M91-E: implement minimum-set sensor ablations.
M91-F: freeze a PPO recipe and run P0/P1 RL comparison.
M91-G: run matched hidden-dynamics wrong-history gates.
```

M90 guarded PPO continuation is deferred until M91-A/B show that the chosen
input profile actually contains the self-ID information the policy is expected
to use.
