# M767 V4 Fresh Source-Holdout Wave Implementation

## Purpose

M767 implements the fresh source-holdout wave designed in M766.

The question is:

```text
Can a disjoint-seed v4 wave create a fresh sequence-outcome corpus for later
M761 residual replay?
```

This milestone is data-generation only:

```text
fresh source wave
fresh sequence intervention
fresh corpus export
no residual replay
no actor training
no residual retraining
no PPO
no checkpoint promotion
```

## Seed Freshness

M767 uses:

```text
seed_start: 76512
seed_count: 512
```

This is disjoint from M749/M752/M755 public source rows:

```text
M749/M752/M755 seed range: 76000..76511
M767 seed range: 76512..77023
```

## Stage 1: Fresh V4 Extreme-Fault Source Wave

Run:

```text
runs/m767_v4_source_holdout_extreme_faults
```

Result:

```text
result_class: cross_fault_reset_only

seed_start: 76512
seed_count: 512
scenario_count: 14848
snapshot_count: 100392
matched_pair_count: 12288
reset_only_rows: 390
history_action_critical_rows: 390
wrong_history_action_critical_rows: 0
reset_history_action_critical_rows: 390
actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
```

This is weaker than M749's `1171` reset-only rows, but it is sufficient for a
fresh sequence-intervention attempt.

## Stage 2: Fresh V4 Reset-Source Sequence Intervention

Run:

```text
runs/m767_v4_source_holdout_sequence_intervention
```

Result:

```text
result_class: v4_reset_source_balance_blocked
base_result_class: sequence_source_balance_blocked

source_candidate_rows: 441
source_reset_rows: 390
source_sentinel_rows: 51
source_unique_seeds: 31
source_unique_preferred_fault_families: 9
source_unique_fault_family_pairs: 21
source_max_seed_dominance: 0.204082
source_max_preferred_family_dominance: 0.238095
source_sentinel_fraction: 0.115646

rollout_rows: 10584
sequence_action_critical_rows: 4707
sequence_outcome_critical_rows: 995
unique_sequence_action_seeds: 31
unique_sequence_outcome_seeds: 25
unique_sequence_outcome_fault_family_pairs: 13
max_sequence_outcome_seed_dominance: 0.247236

normal_failed_rejected: 0
sentinel_false_positive_rows: 0
sentinel_false_positive_rate: 0.0
normal_history_retention_pass: true

actor_parameters_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
```

The sequence intervention creates many fresh outcome rows, but misses source
balance thresholds because the fresh source pool is smaller and more
concentrated than M752.

## Stage 3: Fresh V4 Sequence-Outcome Corpus Export

Run:

```text
runs/m767_v4_source_holdout_corpus_export
```

Result:

```text
result_class: v4_sequence_outcome_corpus_sparse

source_summary_result_class: v4_reset_source_balance_blocked
rollout_rows: 10584
sequence_critical_input_rows: 4707
sentinel_input_rows: 1224
raw_positive_candidates: 995
sentinel_positive_candidates: 0
positive_rows: 995
positive_sentinel_rows: 0
duplicate_positive_keys: 0
missing_normal_matches: 0
positive_rows_missing_v4_metadata: 0
positive_rows_missing_fidelity_metadata: 0

unique_positive_seeds: 25
unique_positive_fault_family_pairs: 13
max_positive_seed_dominance: 0.247236
max_positive_fault_family_pair_dominance: 0.265327

positive_variants:
  reset_hidden_each_step
  zero_command_obs
positive_horizons:
  2
  4
  6
  8
positive_claim_boundary_levels:
  current_model_or_proxy

normal_rows: 995
positive_intervention_rows: 995
hard_negative_rows: 1028
positives_without_hard_negative: 150
hard_negative_complete: true
hard_negative_rows_capped_by_positive: 995

positive_corpus_gate_pass: false
v4_metadata_gate_pass: true
training_started: false
optimizer_started: false
checkpoint_loaded: false
ppo_used: false
promoted: false
```

Registered corpus gates failed:

```text
min_positive_rows: 1000
actual_positive_rows: 995

min_unique_positive_fault_family_pairs: 16
actual_unique_positive_fault_family_pairs: 13

max_allowed_positive_seed_dominance: 0.2
actual_max_positive_seed_dominance: 0.247236
```

## Supported Claims

M767 supports:

```text
1. A disjoint-seed fresh v4 wave can reproduce a large number of sequence
   outcome rows without training or actor mutation.

2. The fresh corpus has clean metadata: no sentinel positives, no duplicate
   positive keys, no missing normal matches, and no missing v4/fidelity
   metadata.

3. Hard-negative contrast is reasonably available on the fresh corpus, with
   1028 hard-negative rows and capped hard negatives for 995 positives.
```

## Falsified Claims

M767 falsifies:

```text
1. The source-holdout replay can proceed immediately after M766 without a data
   quality audit.

2. The disjoint-seed wave trivially matches the public M752/M755 source balance.

3. Fresh source generation is empty.
```

M767 does not prove:

```text
1. M761 residual generalization.

2. Residual closed-loop replay on the fresh corpus.

3. PPO safety or checkpoint promotability.

4. True four-wheel / single-wheel fault physics.
```

## Failure Taxonomy Summary

Primary:

```text
scenario_sampling_failure
```

Reason:

```text
The fresh corpus is large and clean, but it narrowly misses positive-count
threshold, misses fault-family-pair diversity, and exceeds max seed dominance.
```

Not failures:

```text
not metadata_artifact
not contract_violation
not training_instability
not promotion_gate_failure
not private_holdout_contamination
```

## Next Branch Decision

Decision:

```text
v4_sequence_outcome_corpus_sparse_admit_audit
```

M768 should audit whether this fresh corpus is acceptable for a limited
source-holdout residual replay, or whether the next step should be source
balancing / a second fresh wave before replay.

Residual replay, PPO, and checkpoint promotion remain blocked.
