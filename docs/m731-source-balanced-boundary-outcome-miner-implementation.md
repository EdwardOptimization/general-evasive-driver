# M731 Source-Balanced Boundary Outcome Miner Implementation

## Purpose

M731 implements and runs the source-balanced boundary miner designed in M730.

The question is:

```text
Can M728's source-balanced command-history action rows become outcome-critical
when locally relocated near obstacle and terminal-margin boundaries?
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

M731 patches:

```text
src/autodrift/temporal_action_boundary_outcome_miner.py
tests/test_temporal_action_boundary_outcome_miner.py
```

The key fix is schema compatibility for M728 rows:

```text
M722 rows used pair_id.
M728 rows use proposal_id and selected_index.
```

M731 now deduplicates source rows using:

```text
pair_id -> proposal_id -> selected_index -> seed/step/variant/fault fallback
```

It also changes source group ordering from lexicographic key order to balanced
interleaving over:

```text
source_role
preferred_fault_family
wrong_fault_family
fault_family_pair
seed
step bucket
normal margin bucket
action distance bucket
split
severity
source pool
```

This matters because the first attempted full M731 run after the loader fix was
still biased by lexicographic ordering and selected only two preferred families.
The committed result below is from the rerun after balanced group ordering.

## Commands

Smoke:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.temporal_action_boundary_outcome_miner \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_coverage_v2_scenarios.json \
  --temporal-rows runs/m728_quota_calibrated_source_balanced_temporal_wave/temporal_critical_rows.csv \
  --seed-start 72000 \
  --seed-count 16 \
  --max-source-rows 32 \
  --max-candidates-per-source 4 \
  --obstacle-x-shifts=-16,-12,-8,-4,0,4,8 \
  --obstacle-y-shifts=-1.00,-0.75,-0.50,-0.25,0,0.25,0.50,0.75,1.00 \
  --half-width-deltas=0,0.10,0.20,0.30 \
  --device cpu \
  --run-dir runs/m731_source_balanced_boundary_outcome_miner_smoke
```

Registered run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.temporal_action_boundary_outcome_miner \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_coverage_v2_scenarios.json \
  --temporal-rows runs/m728_quota_calibrated_source_balanced_temporal_wave/temporal_critical_rows.csv \
  --seed-start 72000 \
  --seed-count 512 \
  --max-source-rows 512 \
  --max-candidates-per-source 16 \
  --obstacle-x-shifts=-16,-12,-8,-4,0,4,8 \
  --obstacle-y-shifts=-1.00,-0.75,-0.50,-0.25,0,0.25,0.50,0.75,1.00 \
  --half-width-deltas=0,0.10,0.20,0.30 \
  --device cpu \
  --run-dir runs/m731_source_balanced_boundary_outcome_miner
```

## Artifacts

```text
runs/m731_source_balanced_boundary_outcome_miner/summary.json
runs/m731_source_balanced_boundary_outcome_miner/source_rows.csv
runs/m731_source_balanced_boundary_outcome_miner/candidate_variants.csv
runs/m731_source_balanced_boundary_outcome_miner/intervention_rollouts.csv
runs/m731_source_balanced_boundary_outcome_miner/accepted_rows.csv
runs/m731_source_balanced_boundary_outcome_miner/rejected_rows.csv
runs/m731_source_balanced_boundary_outcome_miner/variant_summary.csv
runs/m731_source_balanced_boundary_outcome_miner/fault_family_summary.csv
```

## Result Summary

```text
result_class: temporal_action_only_boundary_sparse

source_candidate_rows:          512
candidate_variant_count:      37248
accepted_rows:                    1

temporal_action_critical_rows: 5881
temporal_outcome_critical_rows:   1

normal_failed_rejected:        2338
history_insensitive_rejected: 31367

sentinel_rows:                 3728
sentinel_false_positive_rows:     0
sentinel_false_positive_rate:   0.0

source_role_counts:
  primary:   459
  secondary:   2
  sentinel:   51

source_unique_seeds: 237
source_unique_preferred_fault_families: 8
source_unique_fault_family_pairs: 30
source_max_seed_dominance: 0.017578
source_max_preferred_family_dominance: 0.126953
source_sentinel_fraction: 0.099609

normal_history_retention_pass: true
actor_parameters_changed:      false
training_started:              false
optimizer_started:             false
ppo_used:                      false
promoted:                      false
```

M731 fixes the M722/M731 source-balance concern:

```text
M722 unique source seeds: 4
M731 unique source seeds: 237

M722 source preferred families: 9 but seed-concentrated
M731 source preferred families: 8 with max family dominance 0.126953
```

## Source Distribution

```text
brake_authority_drop:           65
front_lateral_authority_drop:   65
combined_fault:                 65
delay_noise_fault:              65
drive_authority_drop:           63
global_mu_drop:                 63
mass_cg_shift:                  63
rear_lateral_authority_drop:    63
```

## Variant Breakdown

Dominant temporal action variant:

```text
mismatch_zero_command_history:
  rows:                         8192
  temporal action-critical:     5828
  temporal outcome-critical:       1
  first action distance mean: 0.020667
  first action distance max:  0.035750
  margin gap max:            0.006462
```

Reset hidden:

```text
reset_hidden:
  rows:             8192
  action-critical:  5827
  outcome-critical:    1
  margin gap max:   0.005928
```

Delayed/stale variants:

```text
delayed_hidden_20 temporal action-critical rows: 26
pre_fault_stale_hidden temporal action-critical rows: 27
temporal outcome-critical rows: 0
```

## Accepted Row

M731 finds one accepted temporal boundary row:

```text
source_index: 326
seed: 72248
step: 32
preferred_fault: front_puncture_proxy_extreme_surprise
preferred_fault_family: front_lateral_authority_drop
wrong_fault: puncture_brake_proxy
wrong_fault_family: combined_fault
fault_family_pair: front_lateral_authority_drop->combined_fault
variant: mismatch_zero_command_history

normal_success: true
normal_margin: 0.000389858
variant_success: false
variant_margin: -0.001050173
margin_gap_from_normal: 0.001440031
first_action_distance_from_normal: 0.024997745
terminal_reason: collision

target_obstacle_distance: 9.679901
relocated_obstacle_body_y: -2.062449
relocated_obstacle_half_width: 0.907081
```

This row is useful as a diagnostic seed. It is not enough for an
outcome-positive corpus:

```text
accepted_rows target: >= 20
actual: 1
```

## Interpretation

M731 is a cleaner negative than M722.

M722 was confounded by source concentration. M731 is not:

```text
source rows are broad,
sentinel false positives are zero,
normal retention passes,
actor/input contract is unchanged.
```

The result says:

```text
under the current one-step temporal interventions and local obstacle boundary
relocation, source-balanced action-critical rows almost never become
outcome-critical.
```

This strengthens the case that the blocker is not merely "we did not mine
enough from the same distribution." The next audit should consider whether the
project needs:

```text
1. sequence-level command-response interventions, where the wrong history
   influences several consecutive actions before closed-loop correction;
2. explicit asymmetric/yaw-disturbance dynamics, where faults like tire blowout,
   split-mu, brake pull, and half-shaft loss generate stronger yaw/outcome
   sensitivity;
3. a more aggressive but carefully normal-retained boundary search only if the
   audit finds the current grid still too mild.
```

## Supported Claims

M731 supports:

```text
1. The boundary miner can consume M728 schema rows without collapsing
   proposal_id/selected_index groups.

2. Source-balanced boundary mining finds broad action-critical evidence:
   5881 action-critical rows across a balanced source set.

3. Sentinel false positives are not driving the result.

4. The actor remains sensitive to command-history mismatches at the action
   level.
```

## Falsified Claims

M731 falsifies:

```text
1. M722 failed only because its source pool was seed-concentrated.

2. Source-balanced local obstacle boundary relocation is enough to generate an
   outcome-positive corpus.

3. M731 justifies source export, actor update, PPO, or promotion.
```

M731 does not falsify:

```text
1. Sequence-level temporal interventions may produce stronger outcome
   differences.

2. True asymmetric/yaw-rich dynamics may be required for tire blowout,
   split-mu, brake-pull, and half-shaft loss style failures.

3. The singleton accepted row may still be useful as a diagnostic seed.
```

## Failure Taxonomy

Primary:

```text
metric_artifact
```

Reason:

```text
Action-critical rows remain numerous, but accepted outcome rows remain far
below gate.
```

Secondary:

```text
scenario_sampling_failure
```

Reason:

```text
The current local boundary sampling did not create enough normal-viable,
history-sensitive outcome rows.
```

Not classified as:

```text
contract_violation:
  actor observations were unchanged.

training_instability:
  no training occurred.

proof_washout:
  actor parameters were unchanged.
```

## Next Step

M732 should audit M731 before another experiment.

The audit should decide between:

```text
1. sequence-level command-response intervention design;
2. asymmetric/yaw-disturbance dynamics-fidelity design;
3. one more boundary search only if the current grid is shown to be too mild.
```
