# M1445 Paper-Route Forward Geometry Source Miner Smoke

## Summary

M1445 ran the row-level forward geometry source miner admitted by M1444.

Decision:

```text
forward_geometry_source_miner_pass_route_to_source_step_preflight_support_design
```

M1445 runs only:

```text
autodrift.forward_geometry_source_miner
```

It does not run source preflight, bounded replay, outcome interventions,
training, PPO, promotion, private holdout, corpus export, or actor-input
changes.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.forward_geometry_source_miner \
  --source-geometry-rows runs/m1443_geometry_first_action_enrichment_smoke/selected_enriched_rows.csv \
  --max-candidates 128 \
  --per-seed-cap 24 \
  --per-capability-pair-cap 12 \
  --per-reveal-bucket-cap 12 \
  --per-variant-cap 48 \
  --run-dir runs/m1445_forward_geometry_source_miner_smoke
```

## Results

```text
source_rows: 96
geometry_pass_rows: 3456
selected_candidate_rows: 128
rejected_rows: 0
relocation_clipped_share: 0.0
```

Geometry:

```text
source_body_x min / p50 / p95: 5.065734 / 11.133727 / 14.598930
raw_relocated_body_x min / p50 / p95: 9.065734 / 15.133727 / 18.598930
```

Selected diversity:

```text
unique_source_seeds: 6
unique_capability_pairs: 12
unique_reveal_buckets: 13
unique_variants: 3
max_single_seed_share: 0.1875
max_single_capability_pair_share: 0.09375
```

## Interpretation

M1445 passes the row-level forward geometry miner smoke:

```text
geometry_pass_rows > 0
selected_candidate_rows == 128
relocation_clipped_share == 0.0
source_body_x_min >= 4.0
selected variants >= 2
selected seed/pair/bucket diversity nonzero
```

This confirms that the M1443 source-step enriched rows can be converted into a
forward, unclipped, row-level relocation candidate pool.

M1445 still does not prove history necessity. It only validates a source
candidate layer before source preflight and bounded replay.

## New Missing Layer

The existing `bounded_relocation_replay_probe --preflight-only` reconstructs
candidate traces at `reveal_step`. M1445 candidates are intentionally built from
earlier `source_step` rows. Running the old preflight directly would ignore the
source-step timing that repaired the M1435 source-pool failure.

Therefore the next step is not the old preflight smoke. The next step must first
design source-step-aware preflight/replay support so the replay gate can
evaluate:

```text
candidate_step = source_step
```

instead of silently falling back to:

```text
candidate_step = reveal_step
```

## Guardrails

M1445 guardrail status:

```text
source_preflight_started: false
replay_started: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_input_contract_changed: false
level3_self_id_claim_made: false
```

## Next Route

Admit:

```text
m1446-paper-route-source-step-preflight-support-design
```

M1446 should design the smallest source-step-aware preflight/replay support
needed before any M1445 selected candidate rows are sent to preflight or replay.
