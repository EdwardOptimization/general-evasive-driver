# M1412 Paper-Route Staged Warmup Gate Collision-Stratified Outcome Probe

## Summary

M1412 extended the warmup-latched outcome probe to propagate M1410 warmup gate
source diagnostics into normal/outcome rows, then ran a no-training
collision-stratified outcome probe over all M1410 matched/bucketed rows.

Decision:

```text
staged_warmup_gate_outcome_history_sparse_route_to_result_audit
```

M1412 does not train, run PPO, promote, use private holdout, export a training
corpus, or change actor inputs.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.warmup_latched_outcome_probe \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m1410_staged_warmup_gate_source_wave.json \
  --candidate-rows runs/m1410_staged_warmup_gate_source_smoke/matched_or_bucketed_rows.csv \
  --max-candidate-rows 384 \
  --per-capability-pair-cap 48 \
  --history-length 56 \
  --recent-window-length 4 \
  --max-continuation-steps 48 \
  --min-margin-gap 0.02 \
  --min-sequence-action-l2 0.025 \
  --device cpu \
  --run-dir runs/m1412_staged_warmup_gate_collision_stratified_outcome_probe
```

## Result

```text
result_class: warmup_latched_outcome_history_sparse
selected_candidate_rows: 298
outcome_rows: 2384
normal_margin_candidate_rows: 298
broad_near_boundary_candidate_rows: 53
preferred_near_boundary_candidate_rows: 31
accepted_outcome_rows: 21
warmup_history_positive_rows: 14
accepted_reset_rows: 4
accepted_zero_current_rows: 3
action_critical_rows: 1739
normal_failed_rows: 872
rejected_rows: 0
```

Accepted warmup-history diversity:

```text
rows: 14
unique_source_seeds: 3
unique_capability_pairs: 7
unique_reveal_buckets: 3
unique_variants: 3
max_single_seed_share: 0.714286
max_single_capability_pair_share: 0.214286
```

Preferred near-boundary warmup-history positives are still very sparse:

```text
accepted_warmup_history_preferred_near_boundary_rows: 2
unique_source_seeds: 1
unique_capability_pairs: 2
unique_reveal_buckets: 1
```

Broad near-boundary warmup-history positives:

```text
accepted_warmup_history_broad_near_boundary_rows: 4
unique_source_seeds: 2
unique_capability_pairs: 4
unique_reveal_buckets: 2
```

## Collision Stratification

Collision-source strata:

```text
clear:
  outcome_rows: 688
  outcome_critical_rows: 14
  warmup_history_positive_rows: 10
  unique_seeds: 8
  unique_capability_pairs: 16

clear_low_margin:
  outcome_rows: 176
  outcome_critical_rows: 0
  warmup_history_positive_rows: 0

collision:
  outcome_rows: 1520
  outcome_critical_rows: 7
  warmup_history_positive_rows: 4
  unique_seeds: 19
  unique_capability_pairs: 16
```

This is important: the positive rows are not purely a collision-heavy artifact.
Most warmup-history positives are in the clear source stratum. However, the
positive set remains seed-thin and many positives have high normal margins, so
this is not yet strong self-identification evidence.

Clearance-band strata:

```text
clear_0p00_0p25:
  outcome_rows: 176
  outcome_critical_rows: 0
  warmup_history_positive_rows: 0

clear_0p25_1p00:
  outcome_rows: 512
  outcome_critical_rows: 14
  warmup_history_positive_rows: 10

clear_gt_1p00:
  outcome_rows: 176
  outcome_critical_rows: 0
  warmup_history_positive_rows: 0

collision_negative:
  outcome_rows: 1520
  outcome_critical_rows: 7
  warmup_history_positive_rows: 4
```

## Variant Breakdown

```text
delayed_warmup_history_8: 2 warmup-history-positive rows
delayed_warmup_history_16: 0
wrong_warmup_history_same_reveal: 0
same_recent_wrong_warmup_history: 0
warmup_removed: 7
warmup_shortened_8: 5
reset_hidden: 4 outcome-critical control rows
zero_current_response: 3 outcome-critical control rows
```

The result says that removing or shortening the warmup sometimes changes
outcome, but swapping to wrong warmup history does not yet create robust
outcome-critical errors.

## Interpretation

M1412 is a meaningful improvement over M1405:

```text
M1405 warmup_history_positive_rows: 0
M1412 warmup_history_positive_rows: 14
```

But it remains below the public-positive threshold:

```text
required for positive public result:
  warmup_history_positive_rows >= 48
  accepted_history_seeds >= 12
  accepted_history_capability_pairs >= 6
  accepted_history_reveal_buckets >= 4

observed:
  warmup_history_positive_rows: 14
  accepted_history_seeds: 3
  accepted_history_capability_pairs: 7
  accepted_history_reveal_buckets: 3
```

M1412 therefore supports only a weak claim:

```text
staged warmup gate can create sparse outcome-relevant warmup-history effects.
```

It does not support:

```text
source-diverse history necessity;
wrong-warmup self-identification;
training corpus export;
PPO continuation;
promotion;
level3 self-identification.
```

## Next

M1413 should audit the result before any new run. The likely route is not
training, but a retargeted public source/outcome design that preserves the
clear-stratum signal while increasing near-boundary and seed diversity.

M1413 should decide whether to:

```text
1. retune the gate to lower collision pressure and target clear_0p25_1p00 rows;
2. retarget source selection toward preferred/broad near-boundary candidates;
3. add a wrong-warmup-sensitive objective only after source-diverse outcome rows exist;
4. stop this branch if the signal remains seed-thin after a retargeted repeat.
```
