# M739 Extreme-Fault Distribution V3 Design

## Purpose

M739 turns the coverage hypothesis into the next registered branch:

```text
Maybe the current self-ID evidence is still limited because the scenario
distribution does not cover enough extreme and asymmetric vehicle failures.
```

This milestone is design/config-only:

```text
no full data wave
no actor training
no objective update
no PPO
no checkpoint promotion
no actor-input change
```

It adds:

```text
configs/extreme_fault_distribution_v3_scenarios.json
```

## Why This Branch Now

M734 and M737 produced the first clean positive sequence-outcome evidence:

```text
M734 non-sentinel outcome rows: 70
M737 positive corpus gate: pass
```

But M737 also showed that the current source surface is not yet a complete
contrast corpus:

```text
positive rows: 70
same-source/same-horizon hard negatives: 63
result_class: sequence_outcome_corpus_hard_negative_sparse
```

That makes immediate objective design risky. Training a loss directly on this
fixed public corpus could overfit the known rows instead of discovering a
general driver-like self-identification mechanism.

The user's hypothesis is therefore treated as the next best research question:

```text
Have we simply not generated enough extreme, high-consequence, matched
counterfactual cases?
```

## Model-Fidelity Boundary

The current simulator is still a single-track model. M739 keeps the evidence
boundary explicit.

Current-model faults:

```text
global friction change
brake authority change
drive authority change
steering lag / rate / authority change
mass, CG, and yaw-inertia shift
```

Current-model proxy faults:

```text
front / rear lateral authority collapse as tire or axle authority proxy
split-mu as low-mu plus axle/steering authority proxy
halfshaft or driveline loss as drive authority proxy
actuator delay or deadzone as tau / rate proxy
combined low-mu / brake / steering / axle authority loss
```

Future-only faults:

```text
true single-wheel puncture or blowout
true single-wheel grip collapse
true left/right split-mu patch
true stuck-caliper or single-wheel brake pull
true single-wheel brake pressure loss
true asymmetric half-shaft torque loss
per-wheel ABS fault
wheel-speed sensor drop or bias
tire pressure / temperature / wear dynamics
corner suspension damage
road-crown or bank-induced wheel-load asymmetry
combined single-corner damage
```

The v3 config may use proxies for scenario mining. It must not claim that the
single-track model physically proves true single-wheel blowout or halfshaft
failure behavior.

## V3 Config

Config:

```text
configs/extreme_fault_distribution_v3_scenarios.json
```

Registered scale:

```text
fault specs: 32
future_only_faults: 12
pairing_rules: 40
max_pairs: 8192
max_snapshots_per_scenario: 6
max_steps: 320
max_continuation_steps: 60
snapshot_stride: 3
```

V3 changes from v2:

```text
1. makes fault-onset timing a first-class axis:
   preexisting, warmup, pre-emergency, emergency-entry, recovery

2. adds stricter capability-collapse variants:
   extreme mu, front/rear lateral authority, brake, drive, steering, delay

3. explicitly records scenario difficulty buckets:
   healthy-margin, near-boundary, AEB-infeasible, drift-required, mitigation-only

4. records public/holdout split policy in config metadata;

5. keeps future-only true per-wheel failures out of current-model faults.
```

## Fault Families

Current v3 families:

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

Pairing rules cover cross-family ambiguity, including:

```text
global_mu_drop <-> front/rear lateral authority
global_mu_drop <-> brake authority
front/rear lateral authority <-> steering fault
brake authority <-> steering fault
drive authority <-> rear lateral authority
mass/CG shift <-> brake and front authority
delay/noise <-> steering and brake
combined faults <-> all major single-family faults
```

The purpose is to mine cases that look similar in current ego/scene geometry
but require different command-response belief.

## Matched Counterfactual Requirement

M740 must not just produce a crash zoo. It should generate matched
counterfactual cases:

```text
same seed family and obstacle geometry as much as possible
same or close ego-visible state at decision snapshot
different hidden fault condition
normal history vs reset / wrong / zero / delayed history
action and terminal-margin divergence reported separately
```

The v3 data wave should preserve:

```text
source row metadata
fault name, family, severity, activation step, fidelity class
assigned public/holdout split
snapshot obstacle distance and lateral offset
normal margin and terminal reason
reset-history metrics
wrong-history metrics
source-balance metrics
sentinel false-positive metrics
```

## Public And Holdout Policy

M740 should use public rows for daily diagnosis and keep a holdout split for
promotion-level claims.

Initial split policy:

```text
public:
  assigned_split in train/debug
  used for source mining, corpus export, and objective sanity

holdout:
  assigned_split in heldout
  used only for audit or promotion-level validation
  if used to repair a method, rotate before any paper/promotion claim
```

M740 is not a promotion milestone, so it may report holdout counts but should
not tune thresholds from holdout failures.

## M740 Registered Data Wave

M740 should run the v3 distribution as a no-training discovery wave:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.extreme_dynamics_scenario_corpus \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_distribution_v3_scenarios.json \
  --pairing-mode cross_fault \
  --seed-start 73000 \
  --seed-count 512 \
  --device cpu \
  --run-dir runs/m740_extreme_fault_distribution_v3
```

Expected scale:

```text
nominal + faults per seed: 33
seed_count: 512
scenario_count: 17408
max_pairs: 8192
```

M740 may run a one-seed smoke first to validate config and artifact schema. The
smoke must not be used for capability claims.

## Gates

Source generation gate:

```text
scenario_count >= 16000
matched_pair_count >= 4096
unique_seeds >= 256
unique_preferred_fault_families >= 7
unique_wrong_fault_families >= 7
unique_fault_family_pairs >= 24
future_only_fault_count >= 10
actor_parameters_changed == false
training_started == false
ppo_used == false
promoted == false
```

Reset/history diagnostic gate:

```text
reset_history_critical_rows >= 40
or wrong_history_action_critical_rows >= 40
or sequence-candidate rows >= 80
```

Outcome-positive gate:

```text
wrong_history_outcome_critical_rows >= 20
or reset_history_outcome_critical_rows >= 20
or sequence_outcome_candidate_rows >= 20
```

If the outcome-positive gate fails but source generation passes, classify the
result as coverage-positive/action-only, not as a training failure.

## Failure Classes

M740 should classify:

```text
extreme_fault_v3_source_positive:
  source generation and diversity gates pass

extreme_fault_v3_sequence_candidate_positive:
  source generation passes and sequence-candidate rows appear

extreme_fault_v3_action_only:
  source generation passes and action-critical rows appear but no outcome rows

extreme_fault_v3_reset_only:
  reset-history rows appear but wrong-history rows do not

extreme_fault_v3_source_balance_blocked:
  diversity or dominance gates fail

extreme_fault_v3_artifact:
  actor checksum, contract, sentinel, or config-fidelity boundary is violated
```

## Claims Allowed

If M740 source gates pass, the project may claim:

```text
The scenario distribution has been broadened into a documented v3 extreme-fault
coverage wave with explicit current-model and future-only boundaries.
```

It may not claim:

```text
the driver improved;
the current single-track model proves true single-wheel blowout behavior;
PPO is admissible;
the policy generalizes to real vehicle dynamics.
```

## Next After M740

If M740 finds outcome-sensitive rows:

```text
audit, then export a v3 sequence-outcome corpus
```

If M740 finds only action-sensitive rows:

```text
audit, then run sequence-level interventions on v3 source rows
```

If M740 stays reset-only or history-insensitive:

```text
audit, then decide between higher-fidelity dynamics, explicit disturbance
models, or observation/architecture changes
```

No PPO or objective branch should start until M740 has been run and audited.
