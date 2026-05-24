# M752 V4 Reset-Source Sequence Intervention Implementation

## Purpose

M752 implements and runs the no-training v4 reset-source sequence intervention
wave designed in M751.

The question is:

```text
Can M749's broader v4 reset-sensitive extreme-fault source surface become
outcome-sensitive when command-response interventions persist for H steps?
```

This milestone performs no training:

```text
no actor update
no objective update
no PPO
no checkpoint promotion
no actor-input contract change
```

## Implementation

Added:

```text
src/autodrift/v4_reset_source_sequence_intervention.py
tests/test_v4_reset_source_sequence_intervention.py
```

The runner:

```text
1. reads M749 reset_only_rows.csv and rejected_rows.csv;
2. adapts reset-only rows into v4 source rows;
3. selects primary rows from reset_history_action_critical rows;
4. selects sentinel rows from history_insensitive_too_mild rejected rows;
5. balances by source role, seed, preferred/wrong family, fault-family pair,
   severity, split, step, reset-action bucket, margin bucket, and pairing rule;
6. replays sequence-level intervention variants over H in {2,4,6,8};
7. writes source, rollout, critical, sentinel, rejected, and summary artifacts.
```

The v4 source adapter records:

```text
source_kind: v4_reset_source
claim_boundary_level: current_model_or_proxy
source_pool:
  m749_v4_reset_only
  m749_v4_history_insensitive
```

This preserves the v4 claim boundary:

```text
current two-wheel model/proxy extreme faults are runnable;
true single-wheel/four-wheel/high-fidelity fault physics remain future-only.
```

Focused tests verify:

```text
M749 reset rows become primary source rows;
history-insensitive rejected rows become sentinels;
fault_family_pair is reconstructed;
source_kind and claim boundary fields are preserved;
base sequence result classes are mapped to v4 result classes.
```

## Smoke

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.v4_reset_source_sequence_intervention \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_distribution_v4_scenarios.json \
  --reset-rows runs/m749_extreme_fault_distribution_v4/reset_only_rows.csv \
  --rejected-rows runs/m749_extreme_fault_distribution_v4/rejected_rows.csv \
  --seed-start 76000 \
  --seed-count 64 \
  --max-source-rows 64 \
  --horizons 2,4 \
  --device cpu \
  --run-dir runs/m752_v4_reset_source_sequence_intervention_smoke
```

Smoke result:

```text
source_candidate_rows: 64
source_unique_seeds: 15
source_unique_preferred_fault_families: 9
source_unique_wrong_fault_families: 6
source_unique_fault_family_pairs: 18
source_sentinel_fraction: 0.093750

sequence_action_critical_rows: 433
sequence_outcome_critical_rows: 14
unique_sequence_outcome_seeds: 4
unique_sequence_outcome_fault_family_pairs: 8
sentinel_false_positive_rate: 0.0
actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
```

The smoke was schema/runtime validation only. Its `source_balance_blocked`
classification is expected because the source count is intentionally small.

## Registered Run

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.v4_reset_source_sequence_intervention \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_distribution_v4_scenarios.json \
  --reset-rows runs/m749_extreme_fault_distribution_v4/reset_only_rows.csv \
  --rejected-rows runs/m749_extreme_fault_distribution_v4/rejected_rows.csv \
  --seed-start 76000 \
  --seed-count 512 \
  --max-source-rows 512 \
  --horizons 2,4,6,8 \
  --device cpu \
  --run-dir runs/m752_v4_reset_source_sequence_intervention
```

Run directory:

```text
runs/m752_v4_reset_source_sequence_intervention
```

## Result

M752 is strongly positive:

```text
result_class: v4_reset_sequence_outcome_positive
base_result_class: sequence_outcome_positive

source_candidate_rows: 512
source_reset_rows: 461
source_sentinel_rows: 51
source_unique_seeds: 31
source_unique_preferred_fault_families: 9
source_unique_wrong_fault_families: 7
source_unique_fault_family_pairs: 21
source_max_seed_dominance: 0.121094
source_max_preferred_family_dominance: 0.126953
source_sentinel_fraction: 0.099609

rollout_rows: 12288
sequence_action_critical_rows: 5429
sequence_outcome_critical_rows: 1213
unique_sequence_action_seeds: 31
unique_sequence_outcome_seeds: 27
unique_sequence_outcome_fault_family_pairs: 17
max_sequence_outcome_seed_dominance: 0.171476

sentinel_rows: 1224
sentinel_false_positive_rows: 0
sentinel_false_positive_rate: 0.0
normal_history_retention_pass: true
actor_parameters_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
```

## Variant And Horizon Effects

Outcome rows by variant:

```text
zero_command_obs: 1044
reset_hidden_each_step: 169
```

Outcome rows by horizon:

```text
H=2: 25
H=4: 168
H=6: 455
H=8: 565
```

Outcome rows cover:

```text
preferred fault families: 9
wrong fault families: 6
fault-family pairs: 17
outcome seeds: 27
```

Top outcome pairs:

```text
brake_authority_drop->global_mu_drop: 165
front_lateral_authority_drop->combined_fault: 135
mass_cg_shift->front_lateral_authority_drop: 130
steering_fault->front_lateral_authority_drop: 127
global_mu_drop->front_lateral_authority_drop: 115
rear_lateral_authority_drop->combined_fault: 94
drive_authority_drop->rear_lateral_authority_drop: 85
delay_noise_fault->combined_fault: 76
combined_fault->delay_noise_fault: 67
drive_authority_drop->combined_fault: 62
combined_fault->global_mu_drop: 57
mass_cg_shift->brake_authority_drop: 38
```

## Interpretation

M752 gives a clear answer to the coverage question:

```text
Broader v4 extreme-fault coverage plus sequence-level command-response
intervention exposes a larger outcome-sensitive surface than v3.
```

The pattern is now:

```text
M749 cross-fault wrong-history swap:
  0 wrong-history action-critical rows
  1171 reset-only rows

M752 sequence intervention over M749 reset rows:
  5429 action-critical rows
  1213 outcome-critical rows
```

This supports the user's coverage hypothesis:

```text
Some earlier negative evidence was likely caused by insufficient or poorly
targeted extreme-scenario mining, not by the impossibility of command-response
self-identification evidence.
```

The strongest diagnostic remains sustained `zero_command_obs`, which directly
targets the driver-like command-response history loop. Longer horizons expose
more outcome sensitivity, consistent with the idea that self-ID evidence is
trajectory-level rather than one-step-only.

This does not prove a trained driver improved. It is a diagnostic data wave over
the current BC5660 checkpoint, and it is limited to current-model/proxy v4 fault
coverage.

## Failure Taxonomy

Primary:

```text
none
```

Residual risks:

```text
public_gate_overfit
current_model_or_proxy_physics_limit
hard_negative_sparsity_not_yet_audited
```

Not present:

```text
contract_violation
proof_washout
training_instability
promotion_gate_failure
private_holdout_contamination
```

## Artifacts

```text
runs/m752_v4_reset_source_sequence_intervention/summary.json
runs/m752_v4_reset_source_sequence_intervention/source_rows.csv
runs/m752_v4_reset_source_sequence_intervention/intervention_rollouts.csv
runs/m752_v4_reset_source_sequence_intervention/sequence_critical_rows.csv
runs/m752_v4_reset_source_sequence_intervention/sentinel_rows.csv
runs/m752_v4_reset_source_sequence_intervention/rejected_rows.csv
runs/m752_v4_reset_source_sequence_intervention/variant_summary.csv
runs/m752_v4_reset_source_sequence_intervention/horizon_summary.csv
runs/m752_v4_reset_source_sequence_intervention/fault_family_summary.csv
```

## Next Decision

M753 should audit M752 before any corpus export, objective design, actor update,
or PPO.

Likely next branch if the audit agrees:

```text
v4 sequence-outcome corpus export
```

But M753 must decide explicitly between:

```text
1. v4-aware corpus export;
2. fresh v4 repeat or holdout wave;
3. high-fidelity/four-wheel simulator branch;
4. objective sanity design.
```

PPO and checkpoint promotion remain blocked.
