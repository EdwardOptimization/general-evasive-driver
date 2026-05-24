# M722 Temporal Action-Boundary Outcome Miner Implementation

## Purpose

M722 implements and runs the no-training boundary miner designed in M721.

The question is:

```text
Can M719 temporal command-history action deltas become outcome-critical if the
obstacle is locally moved toward collision or boundary decision surfaces?
```

This milestone is diagnostic-only:

```text
no actor training
no objective update
no PPO
no checkpoint promotion
no actor-input change
```

## Implementation

M722 adds:

```text
src/autodrift/temporal_action_boundary_outcome_miner.py
tests/test_temporal_action_boundary_outcome_miner.py
```

The runner:

```text
1. Starts from M719 temporal action-sensitive rows.
2. Adds sentinel rows from sibling M719 intervention_rollouts.csv.
3. Source-balances rows across seed, fault family, severity, source pool, and
   source role.
4. Reruns the required seed/fault scenarios in memory so hidden state and env
   snapshots are real, not reconstructed from CSV.
5. Relocates obstacle snapshots using structured env fields.
6. Evaluates normal, reset, mismatch_zero_command_history, delayed_hidden_20,
   and pre_fault_stale_hidden variants.
7. Accepts a row only when normal history is viable and temporal mismatch is
   both action-critical and outcome-critical.
```

Actor observations remain unchanged. Fault and obstacle metadata are generation
and audit metadata only.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.temporal_action_boundary_outcome_miner \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_coverage_v2_scenarios.json \
  --temporal-rows runs/m719_temporal_action_response_mismatch/temporal_critical_rows.csv \
  --seed-start 72000 \
  --seed-count 512 \
  --device cpu \
  --run-dir runs/m722_temporal_action_boundary_outcome_miner
```

The default registered mining scale is:

```text
max_source_rows:             128
max_candidates_per_source:    12
obstacle_x_shifts:           [-12, -8, -4, 0, +4]
obstacle_y_shifts:           [-0.75, -0.50, -0.25, 0, +0.25, +0.50, +0.75]
half_width_deltas:           [0, +0.10, +0.20]
```

## Artifacts

```text
runs/m722_temporal_action_boundary_outcome_miner/summary.json
runs/m722_temporal_action_boundary_outcome_miner/source_rows.csv
runs/m722_temporal_action_boundary_outcome_miner/candidate_variants.csv
runs/m722_temporal_action_boundary_outcome_miner/intervention_rollouts.csv
runs/m722_temporal_action_boundary_outcome_miner/accepted_rows.csv
runs/m722_temporal_action_boundary_outcome_miner/rejected_rows.csv
runs/m722_temporal_action_boundary_outcome_miner/variant_summary.csv
runs/m722_temporal_action_boundary_outcome_miner/fault_family_summary.csv
```

## Result Summary

```text
result_class: temporal_action_only_boundary_sparse

source_candidate_rows:          128
candidate_variant_count:       6984
accepted_rows:                    0

temporal_action_critical_rows:  921
temporal_outcome_critical_rows:   0

normal_failed_rejected:         660
history_insensitive_rejected:  6063

sentinel_rows:                  732
sentinel_false_positive_rows:     0
sentinel_false_positive_rate:   0.0

source_role_counts:
  primary:   115
  sentinel:   13

normal_history_retention_pass: true
actor_parameters_changed:      false
training_started:              false
optimizer_started:             false
ppo_used:                      false
promoted:                      false
```

Source diversity after M719 source balancing:

```text
unique source seeds: 4

source seed counts:
  72000: 50
  72001: 35
  72002: 30
  72003: 13

preferred fault families:
  combined_fault:                37
  brake_authority_drop:          23
  global_mu_drop:                17
  steering_fault:                12
  drive_authority_drop:          11
  mass_cg_shift:                  9
  rear_lateral_authority_drop:    7
  delay_noise_fault:              6
  front_lateral_authority_drop:   6
```

## Variant Breakdown

```text
mismatch_zero_command_history:
  rows:                         1536
  temporal action-critical:      864
  temporal outcome-critical:       0
  first action distance mean: 0.020037
  first action distance max:  0.030529
  margin gap max:            0.002842

reset_hidden:
  rows:                         1536
  action-critical:               848
  outcome-critical:                0
  first action distance mean: 0.019875
  margin gap max:            0.001957

delayed_hidden_20:
  rows:                         1536
  temporal action-critical:       32
  temporal outcome-critical:       0
  margin gap max:            0.000473

pre_fault_stale_hidden:
  rows:                          840
  temporal action-critical:       25
  temporal outcome-critical:       0
  margin gap max:            0.000188
```

## Interpretation

M722 strengthens the M719/M720 conclusion:

```text
temporal command-history action dependence is real,
but the current source pool and local obstacle relocation grid still do not
convert it into closed-loop margin or success evidence.
```

The negative is not cleanly "no self-identification." It is narrower:

```text
with M719's source rows, and with this local relocation grid, temporal action
deltas remain outcome-neutral.
```

Two details matter:

```text
1. The source pool is seed-concentrated. Even after source balancing, selected
   rows came from only 4 seeds because M719 filled max_pairs early.

2. The local boundary grid can create normal-history failures, but it does not
   create cases where normal succeeds and temporal mismatch fails or loses at
   least 0.02 m of margin.
```

That points away from immediate objective design and toward an audit before the
next branch. Possible next branches are:

```text
fresh source-balanced temporal data wave
more aggressive but controlled obstacle/boundary search
sequence-level or multi-step intervention design
four-wheel / explicit-yaw-disturbance dynamics for true asymmetric faults
```

## Supported Claims

M722 supports:

```text
1. The M722 miner is executable and writes the expected artifacts.

2. The actor checksum and input contract remain unchanged.

3. `mismatch_zero_command_history` remains the strongest temporal action
   intervention under local boundary relocation.

4. Sentinel false positives are not causing the result.

5. Current M719 temporal action rows are insufficient for source-positive
   outcome proof under this boundary miner.
```

## Falsified Claims

M722 falsifies:

```text
1. M719 failed only because obstacle placement was mildly too easy.

2. Local obstacle longitudinal/lateral/width relocation around M719 rows is
   enough to produce temporal outcome-critical rows.

3. M722 justifies source export, actor update, PPO, or checkpoint promotion.
```

M722 does not falsify:

```text
1. A fresh source-balanced temporal data wave may expose better rows.

2. A more explicit four-wheel or yaw-disturbance model may be required for true
   blowout, split-mu, brake-pull, and asymmetric half-shaft failures.

3. A sequence-level action or active probing branch may create larger
   action-to-outcome differences.
```

## Failure Taxonomy

Primary:

```text
scenario_sampling_failure
```

Reason:

```text
The registered boundary miner finds many temporal action-critical rows but zero
outcome-critical rows, and source rows remain concentrated in only 4 seeds.
```

Secondary:

```text
metric_artifact
```

Reason:

```text
It would still be an overclaim to report temporal action-critical rows as
closed-loop self-identification proof.
```

Not classified as:

```text
training_instability:
  no training occurred.

contract_violation:
  actor observations were unchanged.

proof_washout:
  actor parameters were unchanged.
```

## Next Step

M723 should audit this negative before any additional miner expansion.

The audit should decide whether to:

```text
1. regenerate a source-balanced temporal data wave instead of mining M719's
   seed-concentrated rows;
2. expand boundary search with stricter normal-history viability controls;
3. pivot to sequence-level interventions;
4. design a higher-fidelity asymmetric fault branch.
```
