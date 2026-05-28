# M1397 Paper-Route Warmup-Latched Outcome Full Sweep

## Summary

M1397 runs the same no-training M1395 outcome-intervention probe over all M1394
matched/bucketed warmup-latched rows. The purpose is to test whether M1395's
source-narrow positives were caused by the 384-row candidate cap.

Decision:

```text
warmup_latched_full_sweep_history_sparse_route_to_branch_synthesis
```

M1397 does not train, run PPO, promote, use private holdout, export a training
corpus, or change actor inputs.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.warmup_latched_outcome_probe \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m991_capability_step_fault_source_wave.json \
  --candidate-rows runs/m1394_warmup_latched_config_smoke/matched_or_bucketed_rows.csv \
  --max-candidate-rows 0 \
  --per-capability-pair-cap 128 \
  --history-length 36 \
  --recent-window-length 4 \
  --max-continuation-steps 48 \
  --device cpu \
  --run-dir runs/m1397_warmup_latched_outcome_full_sweep
```

## Result

Artifact:

```text
runs/m1397_warmup_latched_outcome_full_sweep/summary.json
```

Counts:

```text
result_class: warmup_latched_outcome_history_sparse
selected_candidate_rows: 604
outcome_rows: 4832
accepted_outcome_rows: 64
warmup_history_positive_rows: 31
accepted_reset_rows: 14
accepted_zero_current_rows: 19
action_critical_rows: 3003
normal_failed_rows: 1160
rejected_rows: 0
```

Evaluated diversity:

```text
unique_source_seeds: 27
unique_capability_pairs: 16
unique_reveal_buckets: 131
```

Accepted warmup-history diversity:

```text
rows: 31
unique_source_seeds: 1
unique_capability_pairs: 9
unique_reveal_buckets: 5
unique_variants: 2
max_single_seed_share: 1.0
```

## Variant Findings

```text
delayed_warmup_history_8: 0 outcome-critical rows
delayed_warmup_history_16: 0 outcome-critical rows
wrong_warmup_history_same_reveal: 0 outcome-critical rows
same_recent_wrong_warmup_history: 0 outcome-critical rows
warmup_removed: 24 warmup-history-positive rows
warmup_shortened_8: 7 warmup-history-positive rows
reset_hidden: 14 outcome-critical control rows
zero_current_response: 19 outcome-critical control rows
```

The full sweep confirms the M1395 pattern. Accepted warmup-history rows become
more capability-pair diverse, but they remain a single-seed pocket and still do
not include wrong-warmup, same-recent wrong-warmup, or delayed-warmup outcome
effects.

## Interpretation

The candidate cap was not the main cause of M1395 sparsity:

```text
M1395:
  evaluated rows: 3072
  accepted warmup-history rows: 12
  accepted seeds: 1
  accepted capability pairs: 3
  accepted reveal buckets: 3

M1397:
  evaluated rows: 4832
  accepted warmup-history rows: 31
  accepted seeds: 1
  accepted capability pairs: 9
  accepted reveal buckets: 5
```

The result is useful negative evidence:

```text
supported: warmup removed/shortened can change clearance margin in one seed pocket.
not supported: source-diverse warmup-history necessity.
not supported: wrong-history self-identification under current warmup/reveal setup.
not supported: delayed-history outcome necessity.
```

M1397 should close this local warmup-latched outcome branch. Continuing to tune
the same public rows would risk gate-passing overfit. The next step should be a
branch synthesis that decides whether to pivot to stronger warmup/reveal pressure,
different source matching, or a new task family.

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
