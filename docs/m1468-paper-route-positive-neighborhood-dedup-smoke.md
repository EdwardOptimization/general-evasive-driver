# M1468 Paper-Route Positive Neighborhood Dedup Smoke

## Summary

M1468 reran the positive-neighborhood proposal smoke after the M1467 dedup
repair.

Decision:

```text
positive_neighborhood_dedup_smoke_pass_route_to_preflight_design
```

M1468 ran proposal generation only. It did not run source preflight, bounded
replay, outcome interventions, training, PPO, promotion, private holdout,
corpus export, or actor-input changes.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.positive_neighborhood_expansion \
  --history-positive-rows runs/m1461_retargeted_source_step_bounded_replay_smoke/history_positive_rows.csv \
  --control-positive-rows runs/m1461_retargeted_source_step_bounded_replay_smoke/control_positive_rows.csv \
  --candidate-pool runs/m1459_retargeted_source_step_preflight_smoke/selected_candidate_rows.csv \
  --max-candidates 192 \
  --per-seed-cap 48 \
  --per-capability-pair-cap 32 \
  --per-anchor-cap 96 \
  --per-variant-cap 96 \
  --run-dir runs/m1468_positive_neighborhood_dedup_smoke
```

## Results

```text
history_positive_anchor_rows: 2
control_positive_rows: 8
candidate_pool_rows: 104
proposal_rows: 24960
selected_candidate_rows: 192
selected_unique_positive_neighborhood_keys: 192
selected_duplicate_positive_neighborhood_key_rows: 0
candidate_step_column: source_step
```

Selected source groups:

```text
anchor_source: 32
neighbor_source: 160
```

Selected diversity:

```text
unique_source_seeds: 5
unique_capability_pairs: 9
unique_reveal_buckets: 8
unique_variants: 3
max_single_seed_share: 0.25
max_single_capability_pair_share: 0.166667
```

## Interpretation

M1468 repairs the M1465 metric artifact. The selected candidate count now
matches the unique positive-neighborhood key count, so it is no longer inflated
by duplicate geometry rows.

This is still proposal evidence only. It admits a preflight-only validation
design over the deduplicated positive-neighborhood candidates.

## Guardrails

M1468 guardrail status:

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
m1469-paper-route-positive-neighborhood-preflight-design
```
