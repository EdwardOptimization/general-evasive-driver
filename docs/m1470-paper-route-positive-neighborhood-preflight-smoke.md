# M1470 Paper-Route Positive Neighborhood Preflight Smoke

## Summary

M1470 ran preflight-only validation over the M1468 deduplicated
positive-neighborhood candidates.

Decision:

```text
positive_neighborhood_preflight_pass_route_to_bounded_replay_design
```

M1470 ran only:

```text
autodrift.bounded_relocation_replay_probe --preflight-only --candidate-step-column source_step
```

It did not run bounded replay, outcome interventions, training, PPO,
promotion, private holdout, corpus export, or actor-input changes.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.bounded_relocation_replay_probe \
  --preflight-only \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m1419_warmup_gate_invasiveness_retune_source_wave.json \
  --candidate-rows runs/m1468_positive_neighborhood_dedup_smoke/positive_neighborhood_candidate_rows.csv \
  --max-candidate-rows 192 \
  --per-capability-pair-cap 32 \
  --per-seed-cap 48 \
  --per-reveal-bucket-cap 24 \
  --per-variant-cap 96 \
  --history-length 56 \
  --min-sequence-action-l2 0.025 \
  --min-source-body-x 4.0 \
  --candidate-step-column source_step \
  --device cpu \
  --run-dir runs/m1470_positive_neighborhood_preflight_smoke
```

## Results

```text
candidate_step_column: source_step
input_rows: 192
history_candidate_rows: 192
geometry_pass_rows: 192
selected_candidate_rows: 171
rejected_rows: 0
relocation_clipped_share: 0.0
source_preflight_started: true
replay_started: false
```

Selected diversity:

```text
unique_source_seeds: 5
unique_capability_pairs: 9
unique_reveal_buckets: 8
unique_variants: 3
max_single_seed_share: 0.274854
max_single_capability_pair_share: 0.140351
```

Unique-key retention:

```text
selected_candidate_rows: 171
unique_positive_neighborhood_key: 171
duplicate_rows: 0
```

Geometry:

```text
source_body_x min / p50 / p95: 5.065734 / 11.133727 / 11.980351
```

## Interpretation

M1470 passes the positive-neighborhood source-step preflight gate. The
deduplicated candidates remain reconstructable, unclipped, source-diverse, and
unique-key preserving after preflight selection.

This is still not replay evidence and does not prove history necessity. It
admits a bounded replay smoke design over the M1470 selected candidates.

## Guardrails

M1470 guardrail status:

```text
source_preflight_started: true
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
m1471-paper-route-positive-neighborhood-bounded-replay-design
```
