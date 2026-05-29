# M1450 Paper-Route Source-Step Preflight Rerun

## Summary

M1450 reran the source-step preflight-only smoke after the M1449 schema repair.

Decision:

```text
source_step_preflight_pass_route_to_bounded_replay_design
```

M1450 ran only:

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
  --candidate-rows runs/m1445_forward_geometry_source_miner_smoke/selected_candidate_rows.csv \
  --max-candidate-rows 128 \
  --per-capability-pair-cap 12 \
  --per-seed-cap 24 \
  --per-reveal-bucket-cap 12 \
  --per-variant-cap 48 \
  --history-length 56 \
  --min-sequence-action-l2 0.025 \
  --min-source-body-x 4.0 \
  --candidate-step-column source_step \
  --device cpu \
  --run-dir runs/m1450_source_step_preflight_rerun
```

## Results

```text
candidate_step_column: source_step
input_rows: 128
history_candidate_rows: 128
geometry_pass_rows: 128
selected_candidate_rows: 128
rejected_rows: 0
relocation_clipped_share: 0.0
replay_started: false
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

Geometry:

```text
source_body_x min / p50 / p95: 5.065734 / 11.133727 / 14.598930
candidate_step min / max: 16 / 40
reveal_step min / max: 48 / 56
```

Selected variants:

```text
warmup_removed: 48
delayed_warmup_history_16: 48
warmup_shortened_8: 32
```

## Interpretation

M1450 passes the source-step preflight gate. It confirms that M1445 selected
candidates remain forward, unclipped, source-diverse, and explicitly anchored at
`source_step` after the schema repair.

This still does not prove history necessity. It only admits a bounded replay
smoke design where actual terminal outcomes can be measured.

## Guardrails

M1450 guardrail status:

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
m1451-paper-route-source-step-bounded-replay-design
```

M1451 should design a bounded replay smoke over M1450 selected candidates using
`--candidate-step-column source_step`, while keeping replay evidence separate
from training or promotion.
