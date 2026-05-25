# M773 V4 Broader Source-Holdout Wave Implementation

## Purpose

M773 runs the broader fresh source-holdout wave designed in M772.

The question is:

```text
Was the previous limited holdout evidence partly limited by sparse extreme
scenario mining coverage?
```

This milestone is data-generation only:

```text
no residual replay
no actor training
no residual retraining
no optimizer
no PPO
no checkpoint promotion
```

## Registered Runs

### Broader extreme source wave

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.extreme_dynamics_scenario_corpus \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json \
  --pairing-mode cross_fault \
  --seed-start 77024 \
  --seed-count 1024 \
  --device cpu \
  --run-dir runs/m773_v4_broader_source_holdout_extreme_faults
```

### Broader reset-source sequence intervention

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_reset_source_sequence_intervention \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json \
  --reset-rows runs/m773_v4_broader_source_holdout_extreme_faults/reset_only_rows.csv \
  --rejected-rows runs/m773_v4_broader_source_holdout_extreme_faults/rejected_rows.csv \
  --seed-start 77024 \
  --seed-count 1024 \
  --max-source-rows 1024 \
  --horizons 2,4,6,8 \
  --device cpu \
  --run-dir runs/m773_v4_broader_source_holdout_sequence_intervention
```

### Broader v4 sequence-outcome corpus export

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_sequence_outcome_corpus_export \
  --summary runs/m773_v4_broader_source_holdout_sequence_intervention/summary.json \
  --rollouts runs/m773_v4_broader_source_holdout_sequence_intervention/intervention_rollouts.csv \
  --sequence-critical-rows runs/m773_v4_broader_source_holdout_sequence_intervention/sequence_critical_rows.csv \
  --sentinel-rows runs/m773_v4_broader_source_holdout_sequence_intervention/sentinel_rows.csv \
  --fault-config configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json \
  --run-dir runs/m773_v4_broader_source_holdout_corpus_export
```

## Stage 1: Extreme Source Wave

Result:

```text
run_dir: runs/m773_v4_broader_source_holdout_extreme_faults
result_class: cross_fault_reset_only

seed_start: 77024
seed_count: 1024
fault_count: 28
future_only_fault_count: 14
scenario_count: 29696
snapshot_count: 201913
matched_pair_count: 24576
unmatched_rows: 73

accepted_rows: 0
reset_only_rows: 1389
rejected_rows: 23187
normal_failed_rejected: 7899
history_insensitive_rejected: 15288

wrong_history_action_critical_rows: 0
reset_history_action_critical_rows: 1389

actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
```

Interpretation:

```text
The broader config materially increases raw reset-source coverage. M767 had
390 reset-only rows; M773 has 1389. The mechanism remains reset/history
intervention driven at this stage, not direct wrong-history accepted rows.
```

## Stage 2: Sequence Intervention

Result:

```text
run_dir: runs/m773_v4_broader_source_holdout_sequence_intervention
result_class: v4_reset_sequence_outcome_positive
base_result_class: sequence_outcome_positive

source_candidate_rows: 1024
source_unique_seeds: 63
source_unique_preferred_fault_families: 9
source_unique_wrong_fault_families: 7
source_unique_fault_family_pairs: 22
source_max_seed_dominance: 0.114258
source_max_preferred_family_dominance: 0.203125
source_reset_rows: 922
source_sentinel_rows: 102

rollout_rows: 24576
sequence_action_critical_rows: 10775
sequence_outcome_critical_rows: 2652
unique_sequence_outcome_seeds: 49
unique_sequence_outcome_fault_family_pairs: 17
max_sequence_outcome_seed_dominance: 0.171569

sentinel_false_positive_rows: 0
sentinel_false_positive_rate: 0.0
normal_history_retention_pass: true

actor_parameters_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
```

Interpretation:

```text
This is the strongest support for the coverage hypothesis. The broader source
wave turns into a much larger sequence-outcome positive surface:
995 positives in M767 versus 2652 outcome-critical rows before export in M773.
```

## Stage 3: Corpus Export

Result:

```text
run_dir: runs/m773_v4_broader_source_holdout_corpus_export
result_class: v4_sequence_outcome_corpus_hard_negative_sparse
source_summary_result_class: v4_reset_sequence_outcome_positive

raw_positive_candidates: 2652
positive_rows: 2652
normal_rows: 2652
positive_intervention_rows: 2652
contrast_groups: 2652
hard_negative_rows: 2134
positives_without_hard_negative: 872
hard_negative_complete: false

sentinel_positive_candidates: 0
positive_sentinel_rows: 0
positive_source_role_sentinel_rows: 0
sentinel_false_positive_rows_exported_as_positive: 0
duplicate_positive_keys: 0
missing_normal_matches: 0
positive_rows_missing_v4_metadata: 0
positive_rows_missing_fidelity_metadata: 0
rejected_rows: 0

unique_positive_seeds: 49
unique_positive_fault_family_pairs: 17
max_positive_seed_dominance: 0.171569
max_positive_fault_family_pair_dominance: 0.208145

positive_variants:
  command_shift_obs
  reset_hidden_each_step
  reset_hidden_then_normal
  zero_command_obs

positive_horizons:
  2
  4
  6
  8

positive_claim_boundary_levels:
  current_model_or_proxy

training_started: false
optimizer_started: false
checkpoint_loaded: false
ppo_used: false
promoted: false
```

## M772 Broad Gate Check

M772 target gates:

```text
positive_rows >= 1500:
  actual 2652 -> pass

unique_positive_seeds >= 40:
  actual 49 -> pass

unique_positive_fault_family_pairs >= 18:
  actual 17 -> fail by 1

max_positive_seed_dominance <= 0.15:
  actual 0.171569 -> fail

max_positive_fault_family_pair_dominance <= 0.22:
  actual 0.208145 -> pass
```

Ordinary artifact gates:

```text
sentinel positives: 0 -> pass
missing normal matches: 0 -> pass
missing v4 metadata: 0 -> pass
missing fidelity metadata: 0 -> pass
claim_boundary_level: current_model_or_proxy -> pass
actor/training/PPO/promotion mutation: none -> pass
```

Exporter classification:

```text
positive_corpus_gate_pass: true
v4_metadata_gate_pass: true
result_class: v4_sequence_outcome_corpus_hard_negative_sparse
```

The exporter result is not `v4_sequence_outcome_corpus_exported` because hard
negatives remain incomplete:

```text
hard_negative_rows: 2134
positive_rows: 2652
positives_without_hard_negative: 872
```

## Coverage Comparison

Against M767:

```text
matched_pair_count:
  M767: 12288
  M773: 24576

reset_only_rows:
  M767: 390
  M773: 1389

source_candidate_rows:
  M767: 441
  M773: 1024

sequence_outcome_critical_rows / positive_rows:
  M767: 995
  M773: 2652

unique_positive_seeds:
  M767: 25
  M773: 49

unique_positive_fault_family_pairs:
  M767: 13
  M773: 17

max_positive_seed_dominance:
  M767: 0.247236
  M773: 0.171569

max_positive_fault_family_pair_dominance:
  M767: 0.265327
  M773: 0.208145
```

This materially supports the hypothesis that earlier verification was partly
coverage-limited. The broader wave does not fully close the broad-gate issue,
but it substantially reduces concentration and increases positives.

## Supported Claims

M773 supports:

```text
1. Extreme source mining coverage was likely limiting the evidence surface.

2. The v4 proxy-fault space can produce a much larger clean sequence-outcome
   corpus without changing actor inputs, checkpoint weights, or training.

3. The broader corpus passes ordinary positive-corpus and metadata gates:
   2652 positives, no sentinel positives, no missing normals, no missing
   metadata, and current_model_or_proxy claim boundary.

4. The result is strong enough for an audit milestone.
```

## Falsified Claims

M773 falsifies:

```text
1. Broader source mining cannot produce many more clean outcome-positive rows.

2. M767's sparse holdout was already representative of the reachable v4
   source-positive surface.

3. Increasing seed count and max_pairs only increases raw rows without
   improving sequence outcome coverage.
```

M773 does not prove:

```text
1. Broad driver generalization.

2. Residual replay retention on this broader corpus.

3. PPO safety.

4. Checkpoint promotion readiness.

5. True four-wheel or single-wheel fault physical fidelity.
```

## Failure Taxonomy

Residual risks:

```text
scenario_sampling_failure
```

Reason:

```text
The broader wave is positive, but strict M772 broad gates do not fully pass:
fault-family pairs are 17 instead of 18, seed dominance is 0.171569 instead of
<= 0.15, and hard negatives remain sparse.
```

Not failures:

```text
not contract_violation
not metric_artifact
not private_holdout_contamination
not proof_washout
not behavior_regression
not training_instability
not promotion_gate_failure
```

## Decision

M773 admits audit only:

```text
m774-v4-broader-source-holdout-wave-audit
```

M774 should decide whether the broader corpus is sufficient for limited
residual replay, or whether source balancing/fault-pair mining should be
improved first.

Residual replay, PPO, training, and promotion remain blocked until M774.
