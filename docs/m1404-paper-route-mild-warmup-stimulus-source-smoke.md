# M1404 Paper-Route Mild Warmup Stimulus Source Smoke

## Summary

M1404 creates the figure-eight mild warmup stimulus configs from M1403 and runs
a no-training source smoke.

Decision:

```text
mild_warmup_source_smoke_structural_pass_admit_margin_banded_outcome_probe
```

M1404 does not run outcome interventions, train, run PPO, promote, use private
holdout, export a training corpus, or change actor inputs.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.warmup_latched_config_smoke \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m1404_mild_warmup_stimulus_source_wave.json \
  --seed-start 140400 \
  --seed-count 48 \
  --reveal-steps 48,56,64,72,80 \
  --history-length 56 \
  --min-warmup-evidence-steps 16 \
  --max-source-rows 6144 \
  --device cpu \
  --run-dir runs/m1404_mild_warmup_stimulus_source_smoke
```

## Result

Artifact:

```text
runs/m1404_mild_warmup_stimulus_source_smoke/summary.json
```

Counts:

```text
result_class: warmup_latched_structural_pass
source_rows: 1528
matched_current_rows: 158
bucketed_current_rows: 188
matched_or_bucketed_reveal_rows: 282
finite_metric_rows: 1528
rejected_rows: 6632
```

All-row source diversity:

```text
unique_source_seeds: 30
unique_capability_pairs: 16
unique_reveal_buckets: 409
max_single_seed_share: 0.09948
max_single_capability_pair_share: 0.09817
```

Matched/bucketed diversity:

```text
rows: 282
unique_source_seeds: 27
unique_capability_pairs: 16
unique_reveal_buckets: 101
max_single_seed_share: 0.14894
max_single_capability_pair_share: 0.09929
```

This passes the M1403 structural thresholds:

```text
source_rows >= 512
matched_or_bucketed_reveal_rows >= 160
unique_source_seeds >= 24
unique_capability_pairs >= 8
unique_reveal_buckets >= 8
finite metrics
```

## Reveal-Step Diagnostics

```text
step 48: rows=468, matched_or_bucketed=118, unique_seeds=30
step 56: rows=650, matched_or_bucketed=118, unique_seeds=21
step 64: rows=322, matched_or_bucketed=46,  unique_seeds=13
step 72: rows=54,  matched_or_bucketed=0,   unique_seeds=4
step 80: rows=34,  matched_or_bucketed=0,   unique_seeds=1
```

Interpretation:

```text
48/56/64 are viable reveal steps.
72/80 mostly collapse for matched/bucketed current rows under this stimulus.
```

## Warmup And Hidden Divergence

M1404 distance summary:

```text
warmup_history_l2_p95: 0.05837
current_hidden_l2_p95: 0.55034
ego_response_l2_p95: 0.41992
scene_context_l2_p95: 0.12297
```

Compared with M1400, M1404 has slightly more matched/bucketed rows and stronger
source diversity, but lower warmup-history and hidden p95 divergence. The value
of the figure-eight stimulus therefore must be judged by outcome pressure, not
source materialization alone.

## Next

M1405 should run a no-training margin-banded outcome probe over:

```text
runs/m1404_mild_warmup_stimulus_source_smoke/matched_or_bucketed_rows.csv
```

M1405 must report:

```text
normal_margin_band_summary.csv
accepted outcome rows split by variant
accepted warmup-history rows split by reveal step and capability pair
strict-vs-bucketed current matching split
near-boundary candidate counts:
  0.00 <= normal_margin <= 0.50
  0.02 <= normal_margin <= 0.25
```

M1405 must not train, export a corpus, use private holdout, promote, or claim
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
