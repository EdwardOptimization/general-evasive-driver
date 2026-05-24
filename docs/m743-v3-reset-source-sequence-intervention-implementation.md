# M743 V3 Reset-Source Sequence Intervention Implementation

## Purpose

M743 implements and runs the no-training sequence intervention wave designed in
M742.

The question is:

```text
Can M740's broad reset-sensitive v3 source surface become outcome-sensitive
when command-response interventions persist for H steps?
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
src/autodrift/v3_reset_source_sequence_intervention.py
tests/test_v3_reset_source_sequence_intervention.py
```

The runner:

```text
1. reads M740 reset_only_rows.csv and rejected_rows.csv;
2. adapts reset-only rows into source rows with reconstructed fault-family and
   severity pairs;
3. selects primary rows from reset_history_action_critical rows;
4. selects sentinel rows from history_insensitive_too_mild rejected rows;
5. balances by seed, fault family, severity, split, step, reset-action bucket,
   margin bucket, and pairing rule;
6. replays sequence-level intervention variants over H in {2,4,6,8};
7. writes source, rollout, critical, sentinel, rejected, and summary artifacts.
```

Focused tests verify:

```text
M740 reset rows become primary source rows;
history-insensitive rejected rows become sentinels;
fault_family_pair is reconstructed;
base sequence result classes are mapped to v3 result classes.
```

## Smoke

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.v3_reset_source_sequence_intervention \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_distribution_v3_scenarios.json \
  --reset-rows runs/m740_extreme_fault_distribution_v3/reset_only_rows.csv \
  --rejected-rows runs/m740_extreme_fault_distribution_v3/rejected_rows.csv \
  --seed-start 73000 \
  --seed-count 64 \
  --max-source-rows 64 \
  --horizons 2,4 \
  --device cpu \
  --run-dir runs/m743_v3_reset_source_sequence_intervention_smoke
```

Smoke result:

```text
source_candidate_rows: 64
source_unique_seeds: 17
source_unique_preferred_fault_families: 9
source_unique_fault_family_pairs: 26
source_sentinel_fraction: 0.09375

sequence_action_critical_rows: 405
sequence_outcome_critical_rows: 6
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
python -m autodrift.v3_reset_source_sequence_intervention \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_distribution_v3_scenarios.json \
  --reset-rows runs/m740_extreme_fault_distribution_v3/reset_only_rows.csv \
  --rejected-rows runs/m740_extreme_fault_distribution_v3/rejected_rows.csv \
  --seed-start 73000 \
  --seed-count 512 \
  --max-source-rows 512 \
  --horizons 2,4,6,8 \
  --device cpu \
  --run-dir runs/m743_v3_reset_source_sequence_intervention
```

Run directory:

```text
runs/m743_v3_reset_source_sequence_intervention
```

## Result

M743 is strongly positive:

```text
result_class: v3_reset_sequence_outcome_positive
base_result_class: sequence_outcome_positive

source_candidate_rows: 512
source_reset_rows: 461
source_sentinel_rows: 51
source_unique_seeds: 25
source_unique_preferred_fault_families: 9
source_unique_wrong_fault_families: 8
source_unique_fault_family_pairs: 30
source_max_seed_dominance: 0.134766
source_max_preferred_family_dominance: 0.123047
source_sentinel_fraction: 0.099609

rollout_rows: 12288
sequence_action_critical_rows: 5304
sequence_outcome_critical_rows: 995
unique_sequence_action_seeds: 25
unique_sequence_outcome_seeds: 20
unique_sequence_outcome_fault_family_pairs: 26
max_sequence_outcome_seed_dominance: 0.169849

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
zero_command_obs: 950
reset_hidden_each_step: 45
```

Outcome rows by horizon:

```text
H=2: 3
H=4: 145
H=6: 370
H=8: 477
```

Outcome rows cover:

```text
preferred fault families: 9
wrong fault families: 8
fault-family pairs: 26
outcome seeds: 20
```

Top outcome pairs:

```text
delay_noise_fault->brake_authority_drop: 100
drive_authority_drop->rear_lateral_authority_drop: 95
steering_fault->front_lateral_authority_drop: 91
global_mu_drop->front_lateral_authority_drop: 90
brake_authority_drop->global_mu_drop: 89
combined_fault->global_mu_drop: 70
mass_cg_shift->front_lateral_authority_drop: 58
rear_lateral_authority_drop->global_mu_drop: 51
mass_cg_shift->combined_fault: 51
```

## Interpretation

M743 gives a clear answer to the coverage question:

```text
Broad v3 extreme-fault coverage plus sequence-level command-response
intervention exposes many outcome-sensitive rows.
```

This does not prove a trained driver has improved. It does show that the
M740 reset-sensitive source surface contains real closed-loop outcome
sensitivity once the intervention persists beyond a single hidden reset.

The pattern is now consistent:

```text
M740 cross-fault wrong-history swap:
  0 wrong-history action-critical rows
  744 reset-only rows

M743 sequence intervention over M740 reset rows:
  5304 action-critical rows
  995 outcome-critical rows
```

The strongest diagnostic remains `zero_command_obs`, which directly targets the
driver-like command-response history loop.

## Failure Taxonomy

Primary:

```text
none
```

Residual risk:

```text
public_gate_overfit risk remains because M743 is still a public diagnostic
wave; objective design and PPO remain blocked until M744 audits source
diversity, sentinels, and next branch choice.
```

## Artifacts

```text
runs/m743_v3_reset_source_sequence_intervention/summary.json
runs/m743_v3_reset_source_sequence_intervention/source_rows.csv
runs/m743_v3_reset_source_sequence_intervention/intervention_rollouts.csv
runs/m743_v3_reset_source_sequence_intervention/sequence_critical_rows.csv
runs/m743_v3_reset_source_sequence_intervention/sentinel_rows.csv
runs/m743_v3_reset_source_sequence_intervention/rejected_rows.csv
runs/m743_v3_reset_source_sequence_intervention/variant_summary.csv
runs/m743_v3_reset_source_sequence_intervention/horizon_summary.csv
runs/m743_v3_reset_source_sequence_intervention/fault_family_summary.csv
```

## Next Decision

M744 should audit M743 before any corpus export or objective design.

Likely next branch:

```text
sentinel-filtered v3 sequence-outcome corpus export
```

But M744 must decide explicitly between:

```text
1. corpus export;
2. repeat validation on a fresh v3 source split;
3. simulator-fidelity branch;
4. objective sanity design.
```

PPO and checkpoint promotion remain blocked.
