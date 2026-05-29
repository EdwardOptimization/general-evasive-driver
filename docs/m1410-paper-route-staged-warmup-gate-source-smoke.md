# M1410 Paper-Route Staged Warmup Gate Source Smoke

## Summary

M1410 ran the first no-training source smoke for the staged slot0 warmup gate
route admitted by M1409.

Decision:

```text
staged_warmup_gate_source_structural_pass_route_to_result_audit
```

M1410 does not run outcome interventions, train, run PPO, promote, use private
holdout, export a training corpus, or change actor inputs.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.warmup_latched_config_smoke \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m1410_staged_warmup_gate_source_wave.json \
  --seed-start 141000 \
  --seed-count 48 \
  --reveal-steps 48,56,64 \
  --history-length 56 \
  --min-warmup-evidence-steps 16 \
  --max-source-rows 6144 \
  --device cpu \
  --run-dir runs/m1410_staged_warmup_gate_source_smoke
```

## Result

```text
result_class: warmup_latched_structural_pass
source_rows: 1690
matched_current_rows: 122
bucketed_current_rows: 228
matched_or_bucketed_reveal_rows: 298
finite_metric_rows: 1690
rejected_rows: 3206
```

Source diversity:

```text
unique_source_seeds: 34
unique_capability_pairs: 16
unique_preferred_fault_families: 9
unique_wrong_fault_families: 9
unique_reveal_buckets: 500
max_single_seed_share: 0.049704
max_single_capability_pair_share: 0.099408
```

Matched/bucketed diversity:

```text
unique_source_seeds: 31
unique_capability_pairs: 16
unique_preferred_fault_families: 9
unique_wrong_fault_families: 9
unique_reveal_buckets: 105
max_single_seed_share: 0.134228
max_single_capability_pair_share: 0.117450
```

Warmup gate diagnostics over all source rows:

```text
warmup_gate_visible_rows: 1690 / 1690
warmup_evidence_rows: 1690 / 1690
preferred_warmup_gate_passed_rows: 1566
wrong_warmup_gate_passed_rows: 1566
warmup_gate_collision_rows: 1070
warmup_response_history_l2_mean: 0.058476
warmup_response_history_l2_p95: 0.124635
warmup_action_history_l2_mean: 0.018808
warmup_action_history_l2_p95: 0.056336
current_hidden_l2_mean: 0.194016
current_hidden_l2_p95: 0.528845
```

Warmup gate diagnostics over matched/bucketed rows:

```text
warmup_gate_visible_rows: 298 / 298
warmup_evidence_rows: 298 / 298
preferred_warmup_gate_passed_rows: 280
wrong_warmup_gate_passed_rows: 280
warmup_gate_collision_rows: 190
warmup_response_history_l2_mean: 0.031943
warmup_response_history_l2_p95: 0.057279
warmup_action_history_l2_mean: 0.006515
warmup_action_history_l2_p95: 0.015199
```

Reveal-step split:

```text
step 48: 532 source rows, 114 matched/bucketed rows
step 56: 812 source rows, 140 matched/bucketed rows
step 64: 346 source rows, 44 matched/bucketed rows
```

All rows have finite source-smoke metrics and the actor parameter checksum did
not change.

## Interpretation

The staged warmup gate is a stronger source-materialization mechanism than the
passive figure-eight warmup. It preserves source diversity, produces matched or
bucketed current reveal rows, and creates measurable warmup command-response
history differences without actor-input changes.

This still is not self-identification evidence. It is source viability only.
The next question is whether these rows produce outcome-relevant wrong-warmup,
delayed-history, removed-warmup, or shortened-warmup gaps.

## Risk

The main risk is that the warmup gate is too invasive:

```text
warmup_gate_collision_rows: 1070 / 1690
matched/bucketed warmup_gate_collision_rows: 190 / 298
```

The warmup gate collision flag is diagnostic and not a terminal condition, but
the high count means the source may be partly driven by a strong obstacle-like
warmup event rather than a mild probing stimulus. This does not invalidate
M1410, but it should be audited before any outcome probe or corpus export.

## Next

M1411 should audit the M1410 result before outcome probing. The audit should
decide whether to:

```text
1. admit a no-training outcome probe on M1410 matched/bucketed rows;
2. retune the warmup gate to reduce collision pressure;
3. split the route into strong-gate and mild-gate source variants.
```

M1411 must not train, run PPO, promote, use private holdout, export a corpus,
change actor inputs, or claim level3 self-identification.
