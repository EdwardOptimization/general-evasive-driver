# M715 Extreme-Fault Coverage Refresh Design

## Purpose

M715 turns the coverage hypothesis into a registered research branch:

```text
Maybe wrong-history self-identification evidence is weak because the current
extreme scenario corpus has not covered enough handling-limit fault cases.
```

This milestone is design/config-only:

```text
no full data wave
no source export
no actor update
no PPO
no checkpoint promotion
no actor-input change
```

It adds the v2 discovery config:

```text
configs/extreme_fault_coverage_v2_scenarios.json
```

## Why This Is Needed

M704 and M707 already built a first extreme-fault path:

```text
M704:
  5120 scenarios
  2048 matched pairs
  27 reset-history-critical rows
  0 wrong-history-critical rows

M707:
  9728 scenarios
  2048 matched cross-fault pairs
  15 reset-only rows
  0 wrong-history-critical rows
```

M710 then found wrong-history information in hidden/fused features but not in
actions or outcomes, while M713 showed the actor head can react to those feature
directions if they are amplified:

```text
M710:
  wrong fused-positive rows: 1365 / 2048
  wrong action-positive rows: 0

M713:
  wrong rows crossing action threshold by alpha <= 4: 164
  unique low-alpha fault-pair groups: 20
```

So the current state is not simply "there is no signal." A plausible remaining
failure mode is:

```text
the scenario corpus has not created enough realistic high-consequence cases
where the hidden vehicle capability belief must change the deployed action.
```

## Model-Fidelity Boundary

The current dynamics is a single-track RWD model. It can honestly represent
vehicle-level or axle-level hidden capability changes:

```text
global surface friction
front / rear lateral authority
brake authority
drive authority
steering authority and lag
mass / inertia / CG shift
actuator delay proxies
combined capability faults
```

It cannot faithfully represent true left/right wheel asymmetry:

```text
true single-wheel blowout
true left/right split-mu
true stuck-caliper pull
true asymmetric half-shaft torque loss
per-wheel ABS or brake pressure faults
corner suspension damage
```

M715 therefore separates:

```text
current_model_fault:
  represented directly by VehicleParams changes.

current_model_proxy:
  an honest capability-loss proxy in the single-track model.

future_only_fault:
  requires a four-wheel model, explicit yaw disturbance model, or higher-fidelity
  dynamics engine before it can support evidence claims.
```

## V2 Coverage Axes

The v2 config broadens the current-model/proxy fault coverage over these axes:

```text
road surface:
  mild/moderate/severe/extreme global mu drops
  pre-existing and surprise activation

tire / axle authority:
  front puncture proxy
  rear puncture proxy
  moderate/severe/extreme authority loss

brake:
  brake fade
  severe brake loss
  surprise brake loss

drive:
  half-shaft proxy
  drive authority collapse
  surprise drive loss

steering:
  lag
  rate limit
  max authority loss
  surprise steering authority loss

vehicle:
  mass increase
  front/rear CG shift
  high yaw inertia

delay:
  drive and steering actuator delay proxies

combined:
  low-mu + brake + steering
  front authority + brake
  rear authority + drive
  split-mu proxy as low-mu/front-authority/steering-lag capability loss
  puncture/brake proxy
  rear blowout spin proxy
  ice patch + drive loss
  loaded vehicle + brake fade
```

The config deliberately does not add any of these labels to actor observation.
They are generation/logging/audit labels only.

## M716 Full Data Wave

M716 should run the v2 config as a no-training discovery wave:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.extreme_dynamics_scenario_corpus \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_coverage_v2_scenarios.json \
  --pairing-mode cross_fault \
  --seed-start 72000 \
  --seed-count 512 \
  --device cpu \
  --run-dir runs/m716_extreme_fault_coverage_refresh
```

The expected scale is roughly:

```text
fault specs: 32
nominal + faults per seed: 33
seed_count: 512
scenario_count: 16896
max_pairs: 4096
```

This is intentionally larger and more diverse than M707:

```text
M707 scenario_count: 9728
M707 max_pairs:      2048
```

M716 may run a tiny config-validation smoke first, but the smoke must not be
used for capability claims.

## Config Validation Smoke

M715 ran a one-seed smoke only to verify that the v2 config loads and executes:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.extreme_dynamics_scenario_corpus \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_coverage_v2_scenarios.json \
  --pairing-mode cross_fault \
  --seed-start 72000 \
  --seed-count 1 \
  --device cpu \
  --run-dir runs/m715_extreme_fault_coverage_v2_config_smoke
```

Smoke result:

```text
scenario_count: 33
snapshot_count: 165
matched_pair_count: 160
unmatched_rows: 0
fault_count: 32
future_only_fault_count: 10
actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
```

The smoke result class was `history_insensitive_too_mild`, which is expected
for a single-seed config check and is not used as evidence about capability.

## Intervention Matrix

M716 should evaluate at least:

```text
normal history
reset hidden
wrong cross-fault history
delayed history if implementation cost is small
```

If delayed history is not implemented in the existing runner, M716 should log it
as a follow-up rather than silently omitting it from the design.

## Acceptance Criteria

The main positive result is:

```text
result_class: cross_fault_wrong_positive
```

The v2 discovery wave should require:

```text
wrong_history_action_critical_rows >= 40
accepted_rows >= 120
unique_preferred_fault_families >= 5
unique_wrong_fault_families >= 5
unique_accepted_severities >= 3
unique_accepted_seeds >= 40
```

A weaker but still useful result is:

```text
feature/action positive but outcome negative
```

That would support returning to the actor-head residual/objective path using
v2 rows.

A negative result is:

```text
reset-only or history-insensitive evidence across the v2 taxonomy
```

That should trigger either:

```text
four-wheel / explicit yaw-disturbance model design
```

or:

```text
objective design that treats M713 as the stronger current evidence
```

but not another small threshold tweak on the same corpus.

## Supported Claims

M715 supports:

```text
1. The project has not exhausted extreme-fault coverage.

2. The next data wave should be broader than M704/M707 and should include
   severity, activation timing, and proxy/fidelity stratification.

3. True single-wheel asymmetric failures remain outside the current single-track
   evidence boundary.

4. The coverage refresh can proceed without changing actor inputs or training.
```

## Falsified Claims

M715 falsifies:

```text
1. It is safe to treat M704/M707 as complete extreme-fault coverage.

2. A bicycle/single-track model can directly support claims about true
   per-wheel blowout, split-mu, stuck-caliper, or asymmetric half-shaft physics.

3. M713 actor-head coupling positivity alone is enough to proceed directly to
   PPO or promotion.
```

## Failure Taxonomy

Primary:

```text
none
```

Registered risk for M716:

```text
scenario_sampling_failure
```

Potential future outcome:

```text
model_fidelity_blocked
```

This is not a contract violation because the actor observation contract is
unchanged.

## Next Branch Decision

Continue with:

```text
m716-extreme-fault-coverage-refresh-implementation
```

M716 should generate the full v2 data wave, write the standard run artifacts,
classify the result, and decide whether the project should:

```text
export source-positive rows
return to actor-head objective design
or upgrade the dynamics model for true wheel-asymmetric faults
```
