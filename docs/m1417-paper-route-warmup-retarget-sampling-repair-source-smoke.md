# M1417 Paper-Route Warmup Retarget Sampling Repair Source Smoke

## Summary

M1417 ran the repaired source smoke admitted by M1416. It preserved the retuned
warmup gate and relaxed only the obstacle sampling filter back toward the M1410
proven-sampleable settings.

Decision:

```text
warmup_retarget_sampling_repair_source_structural_pass_invasiveness_fail_route_to_audit
```

M1417 does not run outcome interventions, train, run PPO, promote, use private
holdout, export a training corpus, or change actor inputs.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.warmup_latched_config_smoke \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m1417_warmup_retarget_sampling_repair_source_wave.json \
  --seed-start 141700 \
  --seed-count 48 \
  --reveal-steps 48,56,64,72 \
  --history-length 56 \
  --min-warmup-evidence-steps 16 \
  --max-source-rows 6144 \
  --device cpu \
  --run-dir runs/m1417_warmup_retarget_sampling_repair_source_smoke
```

## Result

```text
result_class: warmup_latched_structural_pass
source_rows: 1630
matched_current_rows: 78
bucketed_current_rows: 198
matched_or_bucketed_reveal_rows: 250
finite_metric_rows: 1630
rejected_rows: 4898
actor_parameters_changed: false
```

Source diversity:

```text
unique_source_seeds: 38
unique_capability_pairs: 16
unique_preferred_fault_families: 9
unique_wrong_fault_families: 9
unique_reveal_buckets: 496
max_single_seed_share: 0.072393
max_single_capability_pair_share: 0.095092
```

Matched/bucketed diversity:

```text
unique_source_seeds: 33
unique_capability_pairs: 16
unique_preferred_fault_families: 9
unique_wrong_fault_families: 9
unique_reveal_buckets: 90
max_single_seed_share: 0.128000
max_single_capability_pair_share: 0.120000
```

## Warmup Evidence

All source rows and all matched/bucketed rows had visible warmup gate history and
nonzero command-response evidence.

Matched/bucketed warmup evidence:

```text
warmup_gate_visible_rows: 250 / 250
warmup_evidence_rows: 250 / 250
warmup_response_history_l2_mean: 0.032652
warmup_response_history_l2_p95: 0.070585
warmup_action_history_l2_mean: 0.007186
warmup_action_history_l2_p95: 0.020763
```

This passes the M1416 warmup evidence gates:

```text
response_history_l2_p95 >= 0.035
action_history_l2_p95 >= 0.008
```

## Invasiveness

M1417 restores source materialization and reduces all-row collision pressure
versus M1410, but it does not pass the pre-registered matched/bucketed
invasiveness gate.

```text
all source warmup_gate_collision_share: 0.349693
matched/bucketed warmup_gate_collision_share: 0.544000
matched/bucketed collision rows: 136 / 250
matched/bucketed clear rows: 100
matched/bucketed clear_low_margin rows: 14
clear + clear_low_margin matched/bucketed rows: 114
```

M1416 gates:

```text
matched/bucketed warmup_gate_collision_share <= 0.50
clear + clear_low_margin matched/bucketed rows >= 120
```

Observed:

```text
collision share: 0.544000  # fail
clear + clear_low rows: 114  # fail by 6 rows
```

So M1417 is a structural source pass but an invasiveness gate failure.

## Interpretation

M1417 proves the M1416 sampling repair worked:

```text
M1415 source_rows: 0
M1417 source_rows: 1630
```

It also preserves warmup command-response evidence. However, the retuned gate is
still slightly too invasive on the matched/bucketed subset. Running outcome
interventions now would mix useful clear-source cases with too many
collision-source cases and would violate the M1416 pre-registered gate.

## Next

M1418 should audit this result before any outcome probe. The likely next route
is a small parameter retune that preserves the successful sampling repair while
reducing matched/bucketed collision pressure:

```text
preserve obstacle sampling:
  distance_range: [4.0, 20.0]
  half_width_range: [0.90, 1.65]
  max_threshold_score: 0.50

retune only warmup gate invasiveness:
  consider distance_range [12.0, 20.0]
  consider half_width_range [0.20, 0.35]
  consider lateral_offset_range [-2.6, 2.6]
```

M1418 must not run outcome interventions, train, run PPO, promote, use private
holdout, export a corpus, change actor inputs, or claim self-identification from
source materialization.
