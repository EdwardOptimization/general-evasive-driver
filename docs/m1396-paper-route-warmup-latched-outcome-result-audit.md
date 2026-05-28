# M1396 Paper-Route Warmup-Latched Outcome Result Audit

## Summary

M1396 audits the sparse M1395 warmup-latched outcome result before any new
training, corpus export, or source expansion.

Decision:

```text
warmup_latched_outcome_audit_admit_full_sweep_before_redesign
```

M1396 performs no training, PPO, promotion, private holdout, actor-input change,
checkpoint mutation, or corpus export.

## M1395 Evidence

M1395 evaluated:

```text
selected_candidate_rows: 384
outcome_rows: 3072
accepted_outcome_rows: 25
warmup_history_positive_rows: 12
accepted_reset_rows: 6
accepted_zero_current_rows: 7
action_critical_rows: 1927
normal_failed_rows: 752
result_class: warmup_latched_outcome_history_sparse
```

Accepted warmup-history-positive diversity:

```text
unique_source_seeds: 1
unique_capability_pairs: 3
unique_reveal_buckets: 3
unique_variants: 2
max_single_seed_share: 1.0
```

Variant-level finding:

```text
wrong_warmup_history_same_reveal: 0 outcome-critical rows
same_recent_wrong_warmup_history: 0 outcome-critical rows
delayed_warmup_history_8: 0 outcome-critical rows
delayed_warmup_history_16: 0 outcome-critical rows
warmup_removed: 9 warmup-history-positive rows
warmup_shortened_8: 3 warmup-history-positive rows
```

## Classification

The result is a source-narrow warmup-duration signal, not a source-diverse
wrong-history or delayed-history signal.

Current interpretation:

```text
seed_139421_pocket: useful task-design clue, not a corpus source
wrong_warmup_evidence: unsupported
delayed_warmup_evidence: unsupported
warmup_duration_evidence: sparse and seed-narrow
current/recent substitution risk: still high
training admission: blocked
corpus export admission: blocked
```

The accepted rows are all margin-gap rows, not success-drop rows. Both normal
and variant rollouts remain successful. This means the current task pressure is
not yet sharp enough to prove emergency-relevant history necessity.

## Why Not Redesign Immediately

M1395 selected 384 rows from the 604 M1394 matched/bucketed reveal rows. The
evaluated set already spans 27 seeds and 11 capability pairs, so the sparse
result is meaningful, but it is still a capped sweep. Before changing the task,
one no-training full sweep over all M1394 matched/bucketed rows is cheap and
removes a possible sampling explanation.

This is not a blind expansion for positive hunting because:

```text
1. it uses the already materialized M1394 public rows;
2. it does not change thresholds, actor inputs, or interventions;
3. it does not train or export a corpus;
4. it only decides whether sparse evidence is a sampling artifact.
```

## Next Route

M1397 should run the same M1395 probe over all M1394 matched/bucketed rows:

```text
candidate rows: runs/m1394_warmup_latched_config_smoke/matched_or_bucketed_rows.csv
max_candidate_rows: 0
per_capability_pair_cap: 128
history_length: 36
recent_window_length: 4
max_continuation_steps: 48
```

Decision rule:

```text
If M1397 remains source-narrow:
  route to warmup/reveal source redesign or branch synthesis.

If M1397 finds source-diverse warmup-history-positive rows:
  audit variant composition before any corpus export.

If M1397 positives are still only warmup_removed/shortened:
  treat the result as warmup-duration evidence, not wrong-history self-ID.
```

## Guardrails

```text
training_started: false
evaluation_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_input_contract_changed: false
level3_self_id_claim_made: false
```
