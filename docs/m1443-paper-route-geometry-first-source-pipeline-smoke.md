# M1443 Paper-Route Geometry-First Source Pipeline Smoke

## Summary

M1443 runs the no-training public source pipeline smoke admitted by M1442.

Decision:

```text
geometry_first_source_pipeline_smoke_pass_route_to_branch_synthesis_before_row_level_forward_miner
```

M1443 runs only:

```text
trace-backed source geometry materialization
source-step action-divergence enrichment
```

It does not run source preflight, bounded replay, outcome interventions,
training, PPO, promotion, private holdout, corpus export, or actor-input
changes.

## Commands

Source geometry materialization:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.trace_source_geometry_materializer \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m1419_warmup_gate_invasiveness_retune_source_wave.json \
  --source-rows runs/m1419_warmup_gate_invasiveness_retune_source_smoke/matched_or_bucketed_rows.csv \
  --source-step-offsets=-32,-24,-16,-8,0 \
  --max-source-rows 64 \
  --history-length 56 \
  --device cpu \
  --run-dir runs/m1443_trace_source_geometry_materialization_smoke
```

Source-step action enrichment:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.source_action_divergence_enrichment \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m1419_warmup_gate_invasiveness_retune_source_wave.json \
  --source-geometry-rows runs/m1443_trace_source_geometry_materialization_smoke/source_geometry_rows.csv \
  --sequence-horizon 8 \
  --max-candidates 128 \
  --history-length 56 \
  --device cpu \
  --run-dir runs/m1443_geometry_first_action_enrichment_smoke
```

## Results

Materialization:

```text
source_geometry_rows: 320
rejected_rows: 0
unique_source_seeds: 6
unique_capability_pairs: 16
unique_reveal_buckets: 22
source_body_x_min: -1.594269
source_body_x_p50: 5.601419
source_body_x_p95: 12.073402
source_to_reveal_steps_p50: 16.0
```

Enrichment:

```text
enriched_source_geometry_rows: 2880
selected_enriched_rows: 96
rejected_rows: 0
selected_unique_source_seeds: 6
selected_unique_capability_pairs: 16
selected_unique_reveal_buckets: 20
selected_unique_variants: 3
selected_max_single_seed_share: 0.25
selected_max_single_capability_pair_share: 0.125
```

Selected-row geometry and action metrics:

```text
selected_source_body_x_min: 4.090512
selected_source_body_x_p50: 9.310941
selected_source_body_x_max: 14.598930
selected_sequence_action_l2_mean_min: 0.071366
selected_sequence_action_l2_mean_p50: 0.465744
selected_sequence_action_l2_mean_max: 0.725855
selected_first_action_l2_min: 0.085156
selected_first_action_l2_p50: 0.745224
selected_first_action_l2_max: 0.940177
```

Selected variants:

```text
warmup_removed: 48
warmup_shortened_8: 25
delayed_warmup_history_16: 23
```

## Interpretation

M1443 passes the pre-registered nonzero source-pipeline smoke:

```text
materialized source geometry rows > 0
selected enriched rows > 0
no rejected rows
selected source_body_x_min >= 4.0
```

This fixes the M1435/M1436 source-pool timing failure at the source-pipeline
level: instead of trying to reuse late M1425 reveal-step pressure rows, the
pipeline reconstructs earlier source steps and then measures source-step action
divergence.

M1443 does not prove history necessity. It only proves that the geometry-first
source pipeline can produce forward, source-step action-divergent history rows
for the next row-level relocation miner.

## Guardrails

M1443 guardrail status:

```text
source_materialization_started: true
source_enrichment_started: true
source_preflight_started: false
replay_started: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_parameters_changed: false
actor_input_contract_changed: false
level3_self_id_claim_made: false
```

## Next Route

Admit branch synthesis first:

```text
m1444-paper-route-geometry-aware-preflight-validation-synthesis
```

M1444 should synthesize M1434-M1443 before continuing to row-level mining.
If the synthesis promotes to the next branch, the following miner should run on:

```text
runs/m1443_geometry_first_action_enrichment_smoke/selected_enriched_rows.csv
```

It must not run source preflight, bounded replay, outcome interventions,
training, PPO, promotion, private holdout, corpus export, or actor-input
changes.
