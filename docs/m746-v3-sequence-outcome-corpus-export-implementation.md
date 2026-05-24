# M746 V3 Sequence-Outcome Corpus Export Implementation

## Purpose

M746 implements the no-training v3-aware corpus export designed in M745.

The goal is to preserve M743's sequence-outcome evidence as a durable corpus
with explicit row roles:

```text
normal
positive_intervention
hard_negative_action_only
```

No actor training, objective update, PPO, checkpoint loading, checkpoint
promotion, or actor-input change is performed.

## Implementation

Added:

```text
src/autodrift/v3_sequence_outcome_corpus_export.py
tests/test_v3_sequence_outcome_corpus_export.py
```

The v3 exporter:

```text
1. reads M743 rollout, sequence-critical, sentinel, and summary artifacts;
2. selects only non-sentinel sequence_outcome_critical rows with viable normal history;
3. rejects source_role == sentinel rows from positives;
4. rejects duplicate positive identity keys;
5. requires a matched normal row for each positive;
6. exports same-source/same-horizon action-only hard negatives separately;
7. preserves M743 v3 source metadata:
   pair_id, pairing_rule, reset_action_l2_gap, reset_margin_gap,
   history_margin_gap, action_l2_gap, match_distance, feature_distance,
   acceptance_reason, rejection_reason, and source_kind;
8. enriches rows with fault fidelity metadata from
   configs/extreme_fault_distribution_v3_scenarios.json;
9. writes source, variant, horizon, fault-family, sentinel, and contrast
   balance artifacts;
10. writes strict JSON through autodrift.artifacts.write_json.
```

Focused tests verify:

```text
sentinel positives are excluded
action-only rows are hard negatives, not positives
v3 source fields are preserved in positive and contrast rows
fault fidelity classes and params are added from the config
artifact failures classify before balance failures
hard-negative sparsity is separate from core positive corpus validity
```

## Registered Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.v3_sequence_outcome_corpus_export \
  --summary runs/m743_v3_reset_source_sequence_intervention/summary.json \
  --rollouts runs/m743_v3_reset_source_sequence_intervention/intervention_rollouts.csv \
  --sequence-critical-rows runs/m743_v3_reset_source_sequence_intervention/sequence_critical_rows.csv \
  --sentinel-rows runs/m743_v3_reset_source_sequence_intervention/sentinel_rows.csv \
  --fault-config configs/extreme_fault_distribution_v3_scenarios.json \
  --run-dir runs/m746_v3_sequence_outcome_corpus_export \
  --max-hard-negatives-per-positive 2
```

## Result

Run directory:

```text
runs/m746_v3_sequence_outcome_corpus_export
```

Summary:

```text
result_class: v3_sequence_outcome_corpus_hard_negative_sparse

rollout_rows: 12288
sequence_critical_input_rows: 5304
sentinel_input_rows: 1224

raw_positive_candidates: 995
sentinel_positive_candidates: 0
positive_rows: 995
positive_sentinel_rows: 0
positive_source_role_sentinel_rows: 0
sentinel_false_positive_rows_exported_as_positive: 0
excluded_sentinel_rows: 0
duplicate_positive_keys: 0
missing_normal_matches: 0

positive_rows_missing_v3_metadata: 0
positive_rows_missing_fidelity_metadata: 0
unique_positive_seeds: 20
unique_positive_fault_family_pairs: 26
max_positive_seed_dominance: 0.169849
max_positive_fault_family_pair_dominance: 0.100503

positive_variants:
  reset_hidden_each_step
  zero_command_obs
positive_horizons:
  2, 4, 6, 8
positive_source_kinds:
  v3_reset_source
positive_preferred_fidelity_classes:
  current_model_fault
  current_model_proxy
positive_wrong_fidelity_classes:
  current_model_fault
  current_model_proxy

contrast_groups: 995
normal_rows: 995
positive_intervention_rows: 995
hard_negative_rows: 992
positives_without_hard_negative: 90
hard_negative_complete: false

future_only_fault_count: 12
current_model_fault_count: 12
current_model_proxy_fault_count: 20

positive_corpus_gate_pass: true
v3_metadata_gate_pass: true
training_started: false
optimizer_started: false
checkpoint_loaded: false
ppo_used: false
promoted: false
```

## Corpus Interpretation

The positive corpus passes its registered core gates:

```text
positive_rows >= 500
positive_sentinel_rows == 0
positive_source_role_sentinel_rows == 0
sentinel_false_positive_rows_exported_as_positive == 0
duplicate_positive_keys == 0
missing_normal_matches == 0
normal_rows == positive_rows
contrast_groups == positive_rows
positive_intervention_rows == positive_rows
unique_positive_seeds >= 16
unique_positive_fault_family_pairs >= 16
max_positive_seed_dominance <= 0.20
positive_rows_missing_v3_metadata == 0
positive_rows_missing_fidelity_metadata == 0
```

The same-source/same-horizon hard-negative contrast is slightly sparse:

```text
hard_negative_rows: 992
positive_rows: 995
positives_without_hard_negative: 90
```

This does not invalidate the positive sequence-outcome corpus. It means the
hard-negative portion should not be treated as a complete positive-vs-action-only
contrast set without an audit.

The correct classification is:

```text
positive corpus: exported and usable for audit
hard-negative contrast: sparse and needs audit before objective design
```

## Claim Boundary

The export records:

```text
future_only_fault_count: 12
current_model_fault_count: 12
current_model_proxy_fault_count: 20
```

The current data remain single-track and axle-level/proxy capability changes.
They are useful for self-ID corpus mining, but they must not be overclaimed as
true single-wheel blowout, true split-mu, stuck-caliper, or halfshaft-break
physics.

## Failure Taxonomy

Primary:

```text
scenario_sampling_failure
```

Reason:

```text
The positive corpus is clean, but `3` positives are short of a complete
same-source/same-horizon hard-negative contrast count under the registered cap,
and `90` positive groups have no hard negative candidate.
```

Not failures:

```text
not contract_violation
not proof_washout
not promotion_gate_failure
not training_instability
not metric_artifact
```

## Artifacts

```text
runs/m746_v3_sequence_outcome_corpus_export/summary.json
runs/m746_v3_sequence_outcome_corpus_export/positive_sequence_outcomes.csv
runs/m746_v3_sequence_outcome_corpus_export/contrast_rows.csv
runs/m746_v3_sequence_outcome_corpus_export/hard_negative_rows.csv
runs/m746_v3_sequence_outcome_corpus_export/excluded_sentinel_rows.csv
runs/m746_v3_sequence_outcome_corpus_export/rejected_rows.csv
runs/m746_v3_sequence_outcome_corpus_export/source_balance.csv
runs/m746_v3_sequence_outcome_corpus_export/variant_horizon_balance.csv
runs/m746_v3_sequence_outcome_corpus_export/fault_family_balance.csv
```

## Next Decision

M747 should audit the exported v3 corpus before any objective design.

The audit should decide whether to:

```text
1. accept the positive v3 corpus and design a sequence-outcome objective;
2. repair hard-negative sparsity before objective design;
3. launch a broader v4/four-wheel-fidelity scenario branch before training;
4. repeat v3 sequence export with refreshed sources if public-row overfit risk is too high.
```
