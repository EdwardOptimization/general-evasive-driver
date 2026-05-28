# M1400 Paper-Route Warmup Reveal Pressure Source Smoke

## Summary

M1400 runs a no-training late-reveal source smoke from the M1399 warmup/reveal
pressure redesign.

Decision:

```text
late_reveal_source_smoke_structural_pass_admit_margin_banded_outcome_probe
```

M1400 does not run outcome interventions, train, run PPO, promote, use private
holdout, export a training corpus, or change actor inputs.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.warmup_latched_config_smoke \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m991_capability_step_fault_source_wave.json \
  --seed-start 140000 \
  --seed-count 48 \
  --reveal-steps 64,72,80,88,96 \
  --history-length 48 \
  --min-warmup-evidence-steps 12 \
  --max-source-rows 6144 \
  --device cpu \
  --run-dir runs/m1400_warmup_reveal_pressure_source_smoke
```

## Result

Artifact:

```text
runs/m1400_warmup_reveal_pressure_source_smoke/summary.json
```

Counts:

```text
result_class: warmup_latched_structural_pass
source_rows: 1604
matched_current_rows: 198
bucketed_current_rows: 110
matched_or_bucketed_reveal_rows: 256
finite_metric_rows: 1604
rejected_rows: 6556
```

All-row source diversity:

```text
unique_source_seeds: 24
unique_capability_pairs: 16
unique_reveal_buckets: 349
```

Matched/bucketed diversity:

```text
rows: 256
unique_source_seeds: 23
unique_capability_pairs: 16
unique_reveal_buckets: 92
max_single_seed_share: 0.15625
max_single_capability_pair_share: 0.12109
```

The matched/bucketed seed count is one below the ideal M1399 threshold (`23`
versus `24`), but the run is still structurally useful because rows, capability
pairs, and reveal buckets are well above threshold and no actor contract changes
occurred.

## Reveal-Step Diagnostics

```text
step 64: rows=784, matched_or_bucketed=144, unique_seeds=24
step 72: rows=538, matched_or_bucketed=80,  unique_seeds=18
step 80: rows=260, matched_or_bucketed=32,  unique_seeds=10
step 88: rows=20,  matched_or_bucketed=0,   unique_seeds=3
step 96: rows=2,   matched_or_bucketed=0,   unique_seeds=1
```

Interpretation:

```text
64/72/80 are viable late-reveal steps.
88/96 are mostly too late for reconstructable matched/bucketed source rows.
```

## Comparison To M1394

M1394:

```text
source_rows: 2580
matched_or_bucketed_reveal_rows: 604
matched/bucketed unique_source_seeds: 27
warmup_history_l2_p95: 0.07154
current_hidden_l2_p95: 0.58974
```

M1400:

```text
source_rows: 1604
matched_or_bucketed_reveal_rows: 256
matched/bucketed unique_source_seeds: 23
warmup_history_l2_p95: 0.09223
current_hidden_l2_p95: 0.66495
```

M1400 trades lower source volume for stronger warmup/history divergence. That
is consistent with the branch objective, but outcome probing must verify whether
the stronger divergence actually creates near-boundary outcome gaps.

## Next

M1401 should run or implement a margin-banded outcome probe over:

```text
runs/m1400_warmup_reveal_pressure_source_smoke/matched_or_bucketed_rows.csv
```

Additional M1401 reporting requirements:

```text
normal_margin_band_summary.csv
strict_vs_bucketed accepted-row split
reveal_step accepted-row split
near-boundary candidate counts for:
  0.00 <= normal_margin <= 0.50
  0.02 <= normal_margin <= 0.25
```

M1401 must not train, export a corpus, use private holdout, promote, or claim
self-identification from source materialization alone.

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
