# M1405 Paper-Route Mild Warmup Stimulus Outcome Probe

## Summary

M1405 runs the no-training margin-banded outcome probe over M1404
figure-eight mild warmup stimulus matched/bucketed rows.

Decision:

```text
mild_warmup_outcome_reset_only_route_to_result_audit
```

M1405 does not train, run PPO, promote, use private holdout, export a training
corpus, or change actor inputs.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.warmup_latched_outcome_probe \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m1404_mild_warmup_stimulus_source_wave.json \
  --candidate-rows runs/m1404_mild_warmup_stimulus_source_smoke/matched_or_bucketed_rows.csv \
  --max-candidate-rows 384 \
  --per-capability-pair-cap 48 \
  --history-length 56 \
  --recent-window-length 4 \
  --max-continuation-steps 48 \
  --min-margin-gap 0.02 \
  --min-sequence-action-l2 0.025 \
  --device cpu \
  --run-dir runs/m1405_mild_warmup_stimulus_outcome_probe
```

## Result

Artifact:

```text
runs/m1405_mild_warmup_stimulus_outcome_probe/summary.json
```

Counts:

```text
result_class: warmup_latched_outcome_reset_or_current_only
selected_candidate_rows: 282
outcome_rows: 2256
normal_margin_candidate_rows: 282
broad_near_boundary_candidate_rows: 93
preferred_near_boundary_candidate_rows: 26
accepted_outcome_rows: 2
warmup_history_positive_rows: 0
accepted_reset_rows: 2
accepted_zero_current_rows: 0
action_critical_rows: 1584
normal_failed_rows: 744
```

M1404 improved the normal-margin distribution relative to M1401:

```text
M1401 preferred near-boundary candidates: 0
M1405 preferred near-boundary candidates: 26
```

But M1405 still does not provide warmup-history outcome evidence:

```text
wrong_warmup_history_same_reveal outcome-critical rows: 0
same_recent_wrong_warmup_history outcome-critical rows: 0
delayed_warmup_history_8 outcome-critical rows: 0
delayed_warmup_history_16 outcome-critical rows: 0
warmup_removed outcome-critical rows: 0
warmup_shortened_8 outcome-critical rows: 0
warmup_history_positive_rows: 0
```

## Normal-Margin Bands

```text
negative: 92 candidates
viable_0p00_0p02: 2 candidates
preferred_0p02_0p25: 26 candidates
broad_0p25_0p50: 65 candidates
high_gt_0p50: 97 candidates
```

The preferred window is now populated across:

```text
unique_source_seeds: 6
unique_capability_pairs: 9
unique_reveal_buckets: 12
```

This is useful task-design progress, but the preferred-window candidates did
not produce any outcome-critical intervention rows.

## Accepted Rows

Only two rows are outcome-critical:

```text
variant: reset_hidden
unique_source_seeds: 1
unique_capability_pairs: 1
normal_margin_band: high_gt_0p50
success_drop: false
```

The two accepted rows are margin-gap-only reset-hidden effects in high-margin
states:

```text
seed 140404 step 48 margin gap 0.03327
seed 140404 step 56 margin gap 0.02858
```

They do not support wrong-warmup, delayed-history, or warmup-history necessity.

## Variant Summary

```text
reset_hidden: outcome_critical=2, sequence_action_l2_mean=0.5986
warmup_removed: outcome_critical=0, sequence_action_l2_mean=0.4123
warmup_shortened_8: outcome_critical=0, sequence_action_l2_mean=0.2436
zero_current_response: outcome_critical=0, sequence_action_l2_mean=0.1436
delayed_warmup_history_16: outcome_critical=0, sequence_action_l2_mean=0.0694
delayed_warmup_history_8: outcome_critical=0, sequence_action_l2_mean=0.0385
wrong_warmup_history_same_reveal: outcome_critical=0, sequence_action_l2_mean=0.0228
same_recent_wrong_warmup_history: outcome_critical=0, sequence_action_l2_mean=0.0163
```

Interpretation:

```text
the actor is action-sensitive to reset/removed history;
near-boundary candidates now exist;
wrong/delayed warmup history still does not create outcome differences.
```

## Classification

M1405 is a negative self-ID outcome result:

```text
near-boundary candidate sparsity: improved
action sensitivity: present
warmup-history outcome necessity: not supported
source-diverse accepted warmup-history rows: absent
training admission: blocked
corpus export admission: blocked
```

## Next

M1406 should audit M1405 before another source redesign or any training.

The audit should decide between:

```text
1. config redesign:
   keep the useful near-boundary pressure but increase wrong/delayed warmup
   relevance.

2. task API extension:
   introduce a non-oracle warmup stimulus that creates stronger
   command-response evidence than passive figure-eight curvature.

3. branch synthesis:
   close the current warmup/reveal pressure branch if the repeated evidence is
   action-sensitive but not outcome-history-positive.
```

M1406 must not treat the two reset-only rows as self-identification evidence.

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
level3_self_id_claim_made: false
```
