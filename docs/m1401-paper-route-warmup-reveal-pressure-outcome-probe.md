# M1401 Paper-Route Warmup Reveal Pressure Outcome Probe

## Summary

M1401 implements margin-band reporting for the warmup-latched outcome probe and
runs the no-training outcome probe over M1400 late-reveal matched/bucketed rows.

Decision:

```text
late_reveal_margin_banded_outcome_action_only_route_to_result_audit
```

M1401 does not train, run PPO, promote, use private holdout, export a training
corpus, or change actor inputs.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.warmup_latched_outcome_probe \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m991_capability_step_fault_source_wave.json \
  --candidate-rows runs/m1400_warmup_reveal_pressure_source_smoke/matched_or_bucketed_rows.csv \
  --max-candidate-rows 0 \
  --per-capability-pair-cap 128 \
  --history-length 48 \
  --recent-window-length 4 \
  --max-continuation-steps 48 \
  --device cpu \
  --run-dir runs/m1401_warmup_reveal_pressure_outcome_probe
```

## Result

Artifact:

```text
runs/m1401_warmup_reveal_pressure_outcome_probe/summary.json
```

Counts:

```text
result_class: warmup_latched_outcome_action_only
selected_candidate_rows: 256
outcome_rows: 2048
normal_margin_candidate_rows: 256
broad_near_boundary_candidate_rows: 16
preferred_near_boundary_candidate_rows: 0
accepted_outcome_rows: 0
warmup_history_positive_rows: 0
accepted_reset_rows: 0
accepted_zero_current_rows: 0
action_critical_rows: 1464
normal_failed_rows: 16
rejected_rows: 0
```

Evaluated diversity:

```text
unique_source_seeds: 23
unique_capability_pairs: 16
unique_reveal_buckets: 92
```

Broad near-boundary candidate diversity:

```text
rows: 16
unique_source_seeds: 2
unique_capability_pairs: 6
unique_reveal_buckets: 9
max_single_seed_share: 0.875
```

Preferred near-boundary candidate diversity:

```text
rows: 0
```

## Margin Bands

```text
negative: candidate_rows=2, outcome_critical_rows=0
broad_0p25_0p50: candidate_rows=16, outcome_critical_rows=0
high_gt_0p50: candidate_rows=238, outcome_critical_rows=0
```

No candidate appears in the preferred `0.02 <= normal_margin <= 0.25` window.
Most M1400 late-reveal rows remain high-margin, so late reveal did not create
the near-boundary source distribution requested by M1399.

## Variant Findings

```text
delayed_warmup_history_8: 0 outcome-critical rows
delayed_warmup_history_16: 0 outcome-critical rows
wrong_warmup_history_same_reveal: 0 outcome-critical rows
same_recent_wrong_warmup_history: 0 outcome-critical rows
warmup_removed: 0 outcome-critical rows
warmup_shortened_8: 0 outcome-critical rows
reset_hidden: 0 outcome-critical rows
zero_current_response: 0 outcome-critical rows
```

Action sensitivity is present:

```text
action_critical_rows: 1464
reset_hidden sequence_action_l2_mean: 0.9791
warmup_removed sequence_action_l2_mean: 0.6298
warmup_shortened_8 sequence_action_l2_mean: 0.3336
zero_current_response sequence_action_l2_mean: 0.2278
```

But the margin gaps remain near zero and no variant produces accepted outcome
rows. This is action-only evidence, not outcome-relevant history necessity.

## Interpretation

Late reveal alone is insufficient. It increases action differences and hidden
history divergence, but the scenario still does not produce source-diverse
near-boundary outcome gaps:

```text
near-boundary source goal: not met
wrong-history self-ID evidence: not supported
delayed-history outcome necessity: not supported
warmup-duration outcome evidence: not supported in M1401
training admission: blocked
corpus export admission: blocked
```

M1402 should audit whether the next route is:

```text
1. reveal-grid redesign;
2. mild warmup stimulus design;
3. simulator/task extension for tighter obstacle pressure;
4. branch synthesis if late-reveal pressure is exhausted.
```

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
