# M989 V4 Public Base Capability-Step Fault Design

## Purpose

M989 designs the next branch after M988 closed the config-only extreme scenario
family mining route.

The question is:

```text
Can explicit hidden capability-step/fault events create stronger online
self-identification pressure than static episode-level randomization?
```

M989 is design-only:

```text
no code change
no actor update
no PPO
no checkpoint promotion
no private holdout
no actor-input change
```

Current public-gate base:

```text
runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
```

## Existing Infrastructure

The repository already has a no-training hidden-fault event harness:

```text
src/autodrift/extreme_dynamics_scenario_corpus.py
configs/cross_fault_hidden_condition_scenarios.json
configs/extreme_fault_distribution_v4_scenarios.json
```

This harness can:

```text
1. load a frozen recurrent actor;
2. roll out nominal and faulted scenarios;
3. apply hidden VehicleParams changes at a configured activation_step;
4. collect current observations and recurrent hidden states;
5. inject wrong matched histories;
6. replay normal / wrong-history / reset-hidden continuations;
7. write scenario, pair, rollout, accepted, reset-only, rejected, and fidelity artifacts.
```

M989 should therefore not create a new concept from scratch. The correct next
step is to adapt the existing fault-event corpus workflow to the current M974
public-gate base and the current proof question.

## Capability-Step Semantics

Supported by the current single-track model:

| Family | Current-model meaning | Claim level |
| --- | --- | --- |
| `global_mu_drop` | global road/tire friction drop | current_model_fault |
| `front_lateral_authority_drop` | front axle lateral authority loss | current_model_proxy |
| `rear_lateral_authority_drop` | rear axle lateral authority loss | current_model_proxy |
| `brake_authority_drop` | global brake force loss or brake fade | current_model_fault |
| `drive_authority_drop` | rear drive force loss | current_model_proxy |
| `steering_fault` | steering authority, rate, or lag degradation | current_model_fault |
| `mass_cg_shift` | mass, inertia, or CG shift proxy | current_model_fault/proxy |
| `delay_noise_fault` | actuator/sensor delay proxy through time constants | current_model_proxy |
| `combined_fault` | coupled capability loss | current_model_proxy |

Unsupported as physical claims under the current model:

```text
single-tire puncture or blowout
single-corner grip collapse
left/right split-mu
stuck single caliper or brake pull
single-wheel brake pressure loss
asymmetric half-shaft or CV joint failure
open or locked differential failure
per-wheel ABS fault
wheel-speed sensor failure as physical wheel dynamics
corner suspension/toe damage
tire pressure/temperature/wear/delamination dynamics
```

Those may remain as metadata or proxies only. Physical claims require a
four-wheel/contact-patch dynamics extension or a higher-fidelity vehicle engine.

## Why Step Events

M984-M987 showed that static config-only extreme randomization produces many
action differences but no source-diverse wrong-history outcome sensitivity:

```text
M985 all-action-threshold rows: 15019, accepted_rows: 0
M986 all-action-threshold rows: 10431, accepted_rows: 0
M987 all-action-threshold rows:  7090, accepted_rows: 0
```

The likely issue is not that the actor cannot output different actions. The
issue is that the sampled wrong histories are not damaging enough under the
current scenarios.

Capability-step events should create a stronger causal test:

```text
before event:
  the vehicle response looks consistent with one capability envelope

after event:
  the vehicle response abruptly indicates a different braking/lateral/yaw/delay
  envelope, but the actor is not told the hidden event label

wrong-history intervention:
  inject a hidden state formed under an incompatible capability envelope and
  test whether the emergency action becomes unsafe or lower-margin
```

This better matches the desired claim: the recurrent state is a belief over
what the car can do now, not a memory of a label.

## Event Timing

Use staged activation phases:

| Phase | Purpose |
| --- | --- |
| `preexisting` | baseline capability already changed at reset |
| `warmup` | actor can observe response before the obstacle becomes urgent |
| `pre_emergency` | event occurs shortly before obstacle reveal/decision |
| `emergency_entry` | event occurs as avoidance begins |
| `mid_maneuver` | event occurs after the policy has committed |
| `recovery` | event stresses post-avoidance recovery |

The first current-base smoke should use deterministic activation steps in the
scenario config. Later trainable environments must randomize event timing so a
policy cannot learn a clock shortcut.

## Actor Contract

The event label, family, severity, activation step, and hidden parameters are
not actor inputs.

Allowed actor evidence remains only:

```text
ego kinematics / IMU-like response
actuator state
previous physical commands
ego-frame road/free-space/obstacle geometry
recurrent hidden state formed from past command-response history
```

Hidden fault metadata may be used for:

```text
logging
pairing
source-diversity accounting
training-time weights in future teacher/objective work
diagnostic and oracle baselines
```

It must not enter deployable actor observations.

## M990 Implementation Route

M990 should be a minimal no-training smoke:

```text
1. create configs/m990_capability_step_fault_scenarios.json;
2. reuse src/autodrift/extreme_dynamics_scenario_corpus.py;
3. run the M974 public-gate base with pairing_mode=cross_fault;
4. use a small seed count first to validate checkpoint/config compatibility;
5. require artifact integrity and actor checksum stability;
6. do not require accepted rows in the smoke.
```

M990 command shape:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.extreme_dynamics_scenario_corpus \
  --checkpoint runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt \
  --config configs/m990_capability_step_fault_scenarios.json \
  --pairing-mode cross_fault \
  --seed-start 99000 \
  --seed-count 64 \
  --device auto \
  --run-dir runs/m990_v4_public_base_capability_step_fault_smoke
```

Smoke pass criteria:

```text
scenario_count > 0
snapshot_count > 0
matched_pair_count > 0
scenario_summary.csv exists
matched_cross_fault_pairs.csv exists
intervention_rollouts.csv exists
model_fidelity_limits.md exists
actor_parameters_changed == false
training_started == false
ppo_used == false
promoted == false
```

Accepted wrong-history rows are diagnostic at M990 scale, not required.

## Later Gates

If M990 passes, M991 should run a larger no-training source mining wave.

Suggested source gate:

```text
matched_pair_count >= 2000
unique_preferred_fault_families >= 6
unique_wrong_fault_families >= 6
unique_fault_family_pairs >= 12
unique_seeds >= 32
max_seed_dominance <= 0.25
max_fault_family_pair_dominance <= 0.35
wrong_history_action_critical_rows reported separately
reset_only_rows reported separately
```

Suggested proof-positive gate:

```text
wrong_history_action_critical_rows >= 40
accepted wrong-history outcome rows >= 20
unique accepted fault-family pairs >= 6
accepted max seed dominance <= 0.30
accepted max fault-family-pair dominance <= 0.40
```

If M991 is reset-only or action-only, do not train. Route to a sequence-level
intervention audit instead.

## Future Trainable Environment Route

Only after no-training event evidence exists should the main Gym environment
gain a trainable capability-step config.

Potential later API:

```text
DriftEnvConfig.capability_step_fault:
  enabled
  family_weights
  severity_range
  activation_step_range
  activation_phase
  params_range
  log_metadata_only
```

That later environment feature must preserve the 72-dim P0 actor observation by
default and expose event fields only through `info`.

## Decision

M989 admits M990.

Route:

```text
m990-v4-public-base-capability-step-fault-smoke
```

Do not proceed directly to training, PPO, objective design, or promotion.
