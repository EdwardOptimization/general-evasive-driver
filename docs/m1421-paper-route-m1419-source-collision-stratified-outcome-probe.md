# M1421 Paper-Route M1419 Source Collision-Stratified Outcome Probe

## Summary

M1421 ran the no-training outcome probe admitted by M1420. It used M1419
matched/bucketed rows and preserved warmup-gate collision/source diagnostics.

Decision:

```text
m1419_source_outcome_reset_or_current_only_route_to_result_audit
```

M1421 does not train, run PPO, promote, use private holdout, export a training
corpus, or change actor inputs.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.warmup_latched_outcome_probe \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m1419_warmup_gate_invasiveness_retune_source_wave.json \
  --candidate-rows runs/m1419_warmup_gate_invasiveness_retune_source_smoke/matched_or_bucketed_rows.csv \
  --max-candidate-rows 384 \
  --per-capability-pair-cap 48 \
  --history-length 56 \
  --recent-window-length 4 \
  --max-continuation-steps 48 \
  --min-margin-gap 0.02 \
  --min-sequence-action-l2 0.025 \
  --device cpu \
  --run-dir runs/m1421_m1419_source_collision_stratified_outcome_probe
```

## Result

```text
result_class: warmup_latched_outcome_reset_or_current_only
selected_candidate_rows: 252
outcome_rows: 2016
normal_margin_candidate_rows: 252
broad_near_boundary_candidate_rows: 25
preferred_near_boundary_candidate_rows: 11
accepted_outcome_rows: 1
warmup_history_positive_rows: 0
accepted_reset_rows: 0
accepted_zero_current_rows: 1
action_critical_rows: 1524
normal_failed_rows: 800
rejected_rows: 0
```

Evaluated diversity:

```text
unique_source_seeds: 27
unique_capability_pairs: 16
unique_reveal_buckets: 101
unique_variants: 8
```

The single accepted row is not a warmup-history row:

```text
accepted_outcome_rows: 1
accepted_zero_current_rows: 1
warmup_history_positive_rows: 0
```

## Variant Breakdown

```text
delayed_warmup_history_16: 0
delayed_warmup_history_8: 0
wrong_warmup_history_same_reveal: 0
same_recent_wrong_warmup_history: 0
warmup_removed: 0
warmup_shortened_8: 0
reset_hidden: 0
zero_current_response: 1
```

The result is therefore weaker than M1412:

```text
M1412 warmup_history_positive_rows: 14
M1421 warmup_history_positive_rows: 0
```

## Collision Stratification

Warmup-gate collision strata:

```text
clear:
  outcome_rows: 1392
  outcome_critical_rows: 1
  warmup_history_positive_rows: 0
  unique_seeds: 21
  unique_capability_pairs: 16

clear_low_margin:
  outcome_rows: 32
  outcome_critical_rows: 0
  warmup_history_positive_rows: 0

collision:
  outcome_rows: 592
  outcome_critical_rows: 0
  warmup_history_positive_rows: 0
```

Clearance-band strata:

```text
clear_0p00_0p25:
  outcome_rows: 32
  outcome_critical_rows: 0
  warmup_history_positive_rows: 0

clear_0p25_1p00:
  outcome_rows: 624
  outcome_critical_rows: 1
  warmup_history_positive_rows: 0

clear_gt_1p00:
  outcome_rows: 768
  outcome_critical_rows: 0
  warmup_history_positive_rows: 0

collision_negative:
  outcome_rows: 592
  outcome_critical_rows: 0
  warmup_history_positive_rows: 0
```

## Normal Margin Bands

```text
negative:
  candidate_rows: 79
  outcome_critical_rows: 0

viable_0p00_0p02:
  candidate_rows: 7
  outcome_critical_rows: 0

preferred_0p02_0p25:
  candidate_rows: 11
  outcome_critical_rows: 0

broad_0p25_0p50:
  candidate_rows: 7
  outcome_critical_rows: 0

high_gt_0p50:
  candidate_rows: 148
  outcome_critical_rows: 1
```

The only outcome-critical row appears in the high-normal-margin band and is a
zero-current control effect, not a warmup-history effect.

## Interpretation

M1421 is a negative result for the staged warmup outcome-validation branch.

It supports:

```text
M1419 source rows are evaluable;
the probe preserves stratified diagnostics;
current-frame response masking can still move one high-margin row.
```

It does not support:

```text
source-diverse warmup-history necessity;
wrong-warmup outcome sensitivity;
training corpus export;
PPO continuation;
promotion;
level3 self-identification.
```

The M1419 lower-invasiveness source made the source distribution cleaner, but it
also removed the sparse warmup-history-positive signal seen in M1412.

## Next

M1422 should audit this result before any further experiment:

```text
m1422-paper-route-m1419-outcome-result-audit
```

The audit should decide whether to stop the staged warmup outcome-validation
branch, pivot to another task-design mechanism, or admit a different diagnostic
only with a clearly new evidence axis.

M1422 must not train, run PPO, promote, use private holdout, export a corpus,
change actor inputs, or claim self-identification.
