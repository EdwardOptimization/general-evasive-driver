# M748 V4 Extreme-Fault Coverage Design

## Purpose

M748 turns the M747 audit decision into a concrete v4 coverage branch.

The question is:

```text
Can we broaden extreme scenario mining enough to test whether missing coverage,
rather than missing self-ID signal, is limiting the current evidence?
```

This milestone is design/config-only:

```text
no data wave
no actor training
no objective update
no PPO
no checkpoint loading
no checkpoint promotion
no actor-input change
```

It adds:

```text
configs/extreme_fault_distribution_v4_scenarios.json
```

## Motivation

M746 preserved a clean v3 positive corpus:

```text
positive_rows: 995
unique_positive_seeds: 20
unique_positive_fault_family_pairs: 26
positive_corpus_gate_pass: true
v3_metadata_gate_pass: true
```

But M747 blocked immediate objective/PPO work for two reasons:

```text
1. public-row overfit risk:
   the large v3 corpus is still one public run family;

2. coverage boundary:
   v3 includes single-track current-model and proxy faults, not true
   single-wheel blowout, split-mu, stuck-caliper, halfshaft, wheel-sensor, or
   suspension failures.
```

So M748 addresses the user's current hypothesis directly:

```text
Maybe we still have not mined enough extreme, high-consequence, matched
counterfactual cases.
```

## Claim Levels

V4 uses three claim levels.

```text
current_model_fault:
  Directly represented by current VehicleParams changes in the single-track
  model. Examples: global mu drop, brake authority loss, steering rate/authority
  loss, mass/CG/inertia shift.

current_model_proxy:
  A capability-loss or disturbance proxy in the single-track model. Useful for
  self-ID mining, but not a physical single-wheel claim. Examples: front/rear
  lateral authority collapse as tire/corner grip proxy; drive authority loss as
  halfshaft proxy; combined low-mu/brake/steering losses as split-mu or brake
  pull proxy.

future_four_wheel_or_high_fidelity:
  Requires four-wheel/contact-patch dynamics, per-wheel actuation/sensing, or a
  higher-fidelity engine before physical claims are allowed.
```

This boundary is non-negotiable. V4 may use proxies to mine command-response
history dependence, but any document, table, or paper draft must say they are
proxies unless a four-wheel or high-fidelity dynamics engine is used.

## V4 Config

Config:

```text
configs/extreme_fault_distribution_v4_scenarios.json
```

Registered scale:

```text
fault specs: 28
pairing_rules: 26
future_four_wheel_or_high_fidelity faults: 14
max_pairs: 12288
max_snapshots_per_scenario: 7
max_steps: 340
max_continuation_steps: 70
snapshot_stride: 3
```

The config remains compatible with the current
`autodrift.extreme_dynamics_scenario_corpus` runner by keeping executable
fault families inside the supported current model families:

```text
global_mu_drop
front_lateral_authority_drop
rear_lateral_authority_drop
brake_authority_drop
drive_authority_drop
steering_fault
mass_cg_shift
delay_noise_fault
combined_fault
```

The config adds separate metadata for:

```text
future_four_wheel_or_high_fidelity_faults
proxy_fault_map
claim_boundary
coverage_intent
```

## Fault Coverage

V4 covers these scenario categories:

```text
global road friction:
  extreme preexisting low mu
  sudden ice patch at emergency entry
  wet-to-ice transition mid maneuver

single-corner or tire authority proxies:
  front corner grip collapse proxy
  rear corner grip collapse proxy
  front blowout grip proxy
  rear blowout drive/grip proxy
  front/rear suspension authority proxy

braking faults:
  extreme brake fade
  single-wheel brake pressure loss proxy
  stuck-caliper brake-pull proxy
  low-mu brake-loss combined proxy

driveline faults:
  halfshaft torque-loss proxy
  drive cut mid maneuver
  rear drive/oversteer loss proxy

steering faults:
  steering authority collapse
  steering stuck mid-maneuver proxy
  brake-pull plus steering-delay combined proxy

mass and load faults:
  front-heavy payload
  rear-heavy payload
  high-inertia roof load

latency and sensing proxies:
  extreme actuator/sensor delay
  sensor-delay authority proxy

combined faults:
  split-mu front authority proxy
  split-mu rear oversteer proxy
  blowout low-mu brake proxy
  loaded vehicle brake fade
```

Future-only physical faults are also listed explicitly:

```text
true single-wheel puncture/blowout with radius drag and pull
true single-corner grip collapse
true left/right split-mu patch
true stuck-caliper or single-wheel brake pull
true single-wheel brake pressure loss
true asymmetric halfshaft or CV-joint torque loss
open or locked differential failure
per-wheel ABS fault
wheel-speed sensor drop/bias/quantization
steering rack asymmetry or tie-rod damage
corner suspension damage or toe change
tire pressure/temperature/wear/delamination dynamics
road crown/bank/curbstone induced wheel-load asymmetry
combined single-corner damage
```

## Data-Wave Design For M749

M749 should run a no-training v4 data wave using the existing extreme-dynamics
scenario miner:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.extreme_dynamics_scenario_corpus \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_distribution_v4_scenarios.json \
  --pairing-mode cross_fault \
  --seed-start 76000 \
  --seed-count 512 \
  --device cpu \
  --run-dir runs/m749_extreme_fault_distribution_v4
```

M749 remains a no-training data wave:

```text
no actor update
no objective update
no PPO
no checkpoint promotion
no actor-input change
```

## M749 Gates

Source generation gate:

```text
scenario_rows >= 12000
matched_pairs >= 10000
unique_seeds >= 80
unique_preferred_fault_families >= 8
unique_wrong_fault_families >= 8
unique_fault_family_pairs >= 24
max_seed_dominance <= 0.10
```

Action/outcome discovery gates should be reported separately:

```text
reset_only_rows
wrong_history_action_critical_rows
wrong_history_outcome_critical_rows
accepted_wrong_history_rows
```

M749 should not require wrong-history outcome positives to pass. If it finds
only reset/action rows, the next step should be a v4 sequence-level intervention
branch, mirroring the M740 -> M743 lesson.

Sentinel and contract gates:

```text
sentinel_false_positive_rate <= 0.02
actor_parameters_changed == false
training_started == false
optimizer_started == false
ppo_used == false
promoted == false
future_four_wheel_or_high_fidelity faults are counted only as metadata
```

## Sequence-First Follow-Up

M740 alone did not expose wrong-history action rows:

```text
M740 wrong-history action rows: 0
```

M743 exposed the signal only after sequence-level interventions:

```text
M743 sequence outcome rows: 995
```

So M749 should be interpreted as source mining. If it returns reset-only or
action-only evidence, that is not a dead end. The correct follow-up is:

```text
M749 v4 data wave
  -> audit
  -> v4 reset-source sequence intervention
  -> v4 corpus export
  -> audit
```

Training from M746 or v4 rows should wait until the data is audited and the
public-row overfit risk is controlled.

## Actor Input Contract

Actor inputs remain unchanged:

```text
ego kinematics / IMU-like response
steering / throttle / brake actuator state
previous physical commands
road / free-space / obstacle geometry in ego frame
recurrent hidden state from past command-response history
```

The actor must not receive:

```text
fault label
fidelity class
mu / mass / tire / brake / actuator hidden parameters
AEB/AES/drift-required labels
TTC / required clearance / oracle stopping distance
path error / heading error / path curvature
controller mode
```

Fault metadata may be used only for generation, logging, balancing, and audit.

## Supported Claims

M748 supports:

```text
1. The next research branch should test coverage before training from M746.
2. V4 has a runnable current-model/proxy config for no-training source mining.
3. The project has a durable claim boundary for true per-wheel and asymmetric
   failures.
```

M748 does not support:

```text
1. a trained driver improvement claim;
2. PPO continuation;
3. checkpoint promotion;
4. true single-wheel physical-failure claims;
5. paper-level generalization evidence.
```

## Next Step

M749 should implement/run the no-training v4 data wave and audit whether it
produces broader reset, action, or outcome-sensitive source surfaces.
