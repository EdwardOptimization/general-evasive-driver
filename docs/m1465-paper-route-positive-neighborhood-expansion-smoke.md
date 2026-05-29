# M1465 Paper-Route Positive Neighborhood Expansion Smoke

## Summary

M1465 ran the positive-neighborhood expansion proposal generator implemented in
M1464.

Decision:

```text
positive_neighborhood_expansion_smoke_counts_pass_duplicate_key_repair_required
```

M1465 ran proposal generation only. It did not run source preflight, bounded
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
  --run-dir runs/m1465_positive_neighborhood_expansion_smoke
```

## Results

```text
history_positive_anchor_rows: 2
control_positive_rows: 8
candidate_pool_rows: 104
proposal_rows: 24960
selected_candidate_rows: 192
candidate_step_column: source_step
```

Proposal source groups:

```text
anchor_source: 3840
neighbor_source: 21120
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

Duplicate diagnostic:

```text
selected_candidate_rows: 192
unique_positive_neighborhood_key: 20
duplicate_rows: 172
```

## Interpretation

M1465 proves the expansion generator can build a large, source-diverse proposal
pool without running preflight or replay.

It also exposes an implementation issue: selected row count is inflated by
duplicate `positive_neighborhood_key` rows. This is not acceptable for replay
or corpus export because it would over-weight a small set of geometrically
identical candidates.

The correct next step is not replay. Because this branch reached the workflow
synthesis cadence and M1465 exposed a metric artifact, route to branch
synthesis and then a dedup repair if synthesis continues the branch.

## Guardrails

M1465 guardrail status:

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
m1466-paper-route-boundary-retarget-validation-synthesis
```
