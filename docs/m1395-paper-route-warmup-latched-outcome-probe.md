# M1395 Paper-Route Warmup-Latched Outcome Probe

## Summary

M1395 implements and runs a no-training outcome-intervention probe over the
M1394 warmup-latched matched/bucketed reveal rows.

Decision:

```text
warmup_latched_outcome_history_sparse_route_to_result_audit
```

This is not a training result and not a self-identification proof. It is a
public no-training diagnostic over M1394 rows.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.warmup_latched_outcome_probe \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m991_capability_step_fault_source_wave.json \
  --candidate-rows runs/m1394_warmup_latched_config_smoke/matched_or_bucketed_rows.csv \
  --max-candidate-rows 384 \
  --per-capability-pair-cap 48 \
  --history-length 36 \
  --recent-window-length 4 \
  --max-continuation-steps 48 \
  --device cpu \
  --run-dir runs/m1395_warmup_latched_outcome_probe
```

## Result

Artifact:

```text
runs/m1395_warmup_latched_outcome_probe/summary.json
```

Counts:

```text
result_class: warmup_latched_outcome_history_sparse
selected_candidate_rows: 384
outcome_rows: 3072
accepted_outcome_rows: 25
warmup_history_positive_rows: 12
accepted_reset_rows: 6
accepted_zero_current_rows: 7
action_critical_rows: 1927
normal_failed_rows: 752
rejected_rows: 0
variant_count: 8
```

Evaluated diversity:

```text
unique_source_seeds: 27
unique_capability_pairs: 11
unique_reveal_buckets: 103
```

Accepted warmup-history diversity:

```text
rows: 12
unique_source_seeds: 1
unique_capability_pairs: 3
unique_reveal_buckets: 3
unique_variants: 2
max_single_seed_share: 1.0
```

## Variant Findings

Variant summary:

```text
delayed_warmup_history_8: 0 outcome-critical rows
delayed_warmup_history_16: 0 outcome-critical rows
wrong_warmup_history_same_reveal: 0 outcome-critical rows
same_recent_wrong_warmup_history: 0 outcome-critical rows
warmup_removed: 9 warmup-history-positive rows
warmup_shortened_8: 3 warmup-history-positive rows
reset_hidden: 6 outcome-critical control rows
zero_current_response: 7 outcome-critical control rows
```

All 12 accepted warmup-history-positive rows are from seed `139421`. They are
margin-gap rows, not success-drop rows; normal and variant rollouts both remain
successful. They show that warmup removal/shortening can change outcome margin
in one source pocket, but they do not support source-diverse warmup-history
necessity.

## Interpretation

M1395 confirms that the warmup-latched outcome probe is runnable and produces
intervention diagnostics without changing the actor. The result is still
history-sparse:

```text
public diagnostic positive threshold:
  warmup_history_positive_rows >= 48
  accepted_seeds >= 12
  accepted_capability_pairs >= 6
  accepted_reveal_buckets >= 4

M1395:
  warmup_history_positive_rows = 12
  accepted_seeds = 1
  accepted_capability_pairs = 3
  accepted_reveal_buckets = 3
```

The strongest negative is that the wrong-history variants remain at zero
outcome-critical rows. The only positive history variants are warmup
removed/shortened, and only in one seed. Therefore M1395 does not admit corpus
export, PPO, training, promotion, private holdout, or a stronger
self-identification claim.

## Guardrails

```text
actor_parameters_changed: false
training_started: false
evaluation_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_input_contract_changed: false
```

## Next

M1396 should audit this result before any new source expansion. The audit should
answer:

```text
1. Is the seed-139421 pocket useful as a task-design clue or just a singleton?
2. Are wrong-warmup variants too weak because current/recent frame still
   substitutes for history?
3. Should the next route redesign warmup/reveal timing, reveal pressure, or
   source matching before another outcome probe?
4. Should the branch synthesize if warmup-latched evidence remains sparse?
```
