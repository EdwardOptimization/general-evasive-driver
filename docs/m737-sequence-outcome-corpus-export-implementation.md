# M737 Sequence-Outcome Corpus Export Implementation

## Purpose

M737 implements the no-training corpus export designed in M736.

The goal is to preserve M734's non-sentinel sequence-outcome evidence as a
durable corpus with explicit row roles:

```text
normal
positive_intervention
hard_negative_action_only
```

No actor training, objective update, PPO, checkpoint loading, or promotion is
performed.

## Implementation

Added:

```text
src/autodrift/sequence_outcome_corpus_export.py
tests/test_sequence_outcome_corpus_export.py
```

The exporter:

```text
1. reads M734 rollout, sequence-critical, sentinel, and summary artifacts;
2. selects sequence_outcome_critical rows only when sentinel == false;
3. rejects source_role == sentinel rows from positives;
4. rejects duplicate positive identity keys;
5. requires a matched normal row for each positive;
6. exports optional same-source/same-horizon action-only hard negatives;
7. writes source, variant, horizon, sentinel, and contrast balance artifacts;
8. writes strict JSON through autodrift.artifacts.write_json.
```

Focused test coverage verifies that:

```text
sentinel positives are excluded
action-only rows are hard negatives, not proof positives
artifact failures are classified before balance failures
unbalanced positive sets are classified separately
```

## Registered Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.sequence_outcome_corpus_export \
  --summary runs/m734_sequence_command_response_intervention/summary.json \
  --rollouts runs/m734_sequence_command_response_intervention/intervention_rollouts.csv \
  --sequence-critical-rows runs/m734_sequence_command_response_intervention/sequence_critical_rows.csv \
  --sentinel-rows runs/m734_sequence_command_response_intervention/sentinel_rows.csv \
  --run-dir runs/m737_sequence_outcome_corpus_export \
  --max-hard-negatives-per-positive 2
```

## Result

Run directory:

```text
runs/m737_sequence_outcome_corpus_export
```

Summary:

```text
result_class: sequence_outcome_corpus_hard_negative_sparse

rollout_rows: 12288
sequence_critical_input_rows: 5262
sentinel_input_rows: 1224

raw_positive_candidates: 73
sentinel_positive_candidates: 3
positive_rows: 70
positive_sentinel_rows: 0
positive_source_role_sentinel_rows: 0
excluded_sentinel_rows: 3
duplicate_positive_keys: 0
missing_normal_matches: 0

unique_positive_seeds: 28
unique_positive_fault_family_pairs: 10
max_positive_seed_dominance: 0.085714
positive_variants: reset_hidden_each_step, zero_command_obs
positive_horizons: 4, 6, 8

contrast_groups: 70
normal_rows: 70
positive_intervention_rows: 70
hard_negative_rows: 63
contrast_hard_negative_gate_pass: false

positive_corpus_gate_pass: true
training_started: false
optimizer_started: false
checkpoint_loaded: false
ppo_used: false
promoted: false
```

## Corpus Interpretation

The positive corpus passed its registered core gates:

```text
positive_rows >= 50
positive_sentinel_rows == 0
positive_source_role_sentinel_rows == 0
duplicate_positive_keys == 0
missing_normal_matches == 0
unique_positive_seeds >= 20
unique_positive_fault_family_pairs >= 6
max_positive_seed_dominance <= 0.15
```

The stricter same-source/same-horizon hard-negative contrast count did not pass:

```text
hard_negative_rows: 63
positive_rows: 70
```

This does not invalidate the positive sequence-outcome corpus. It does mean the
hard-negative portion should not be treated as a complete contrast set for a
future sequence-preference objective.

The correct classification is therefore:

```text
positive corpus: exported and usable for audit
hard-negative contrast: sparse and needs audit before objective design
```

## Failure Taxonomy

Primary:

```text
scenario_sampling_failure
```

Reason:

```text
Seven positive contrast groups lack same-source/same-horizon action-only hard
negatives under the M736 cap and selection rule.
```

Not failures:

```text
not contract_violation
not proof_washout
not promotion_gate_failure
not training_instability
```

## Artifacts

```text
runs/m737_sequence_outcome_corpus_export/summary.json
runs/m737_sequence_outcome_corpus_export/positive_sequence_outcomes.csv
runs/m737_sequence_outcome_corpus_export/contrast_rows.csv
runs/m737_sequence_outcome_corpus_export/hard_negative_rows.csv
runs/m737_sequence_outcome_corpus_export/excluded_sentinel_rows.csv
runs/m737_sequence_outcome_corpus_export/rejected_rows.csv
runs/m737_sequence_outcome_corpus_export/source_balance.csv
runs/m737_sequence_outcome_corpus_export/variant_horizon_balance.csv
```

## Next Decision

M738 should audit the exported corpus before any objective design.

The audit should decide whether to:

```text
1. accept the positive corpus and design a positive-vs-normal sequence objective;
2. design a cross-horizon or refreshed-source hard-negative repair export;
3. pivot to an extreme-fault distribution v3 branch before objective work.
```

The user's broader coverage hypothesis remains live: this M737 corpus preserves
the first clean sequence-outcome evidence, but it does not prove that the
current scenario distribution covers enough blowout, split-friction,
driveline, brake, steering, sensor, actuator, and fault-onset cases.
