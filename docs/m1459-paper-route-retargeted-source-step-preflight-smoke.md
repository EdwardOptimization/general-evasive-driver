# M1459 Paper-Route Retargeted Source-Step Preflight Smoke

## Summary

M1459 ran the preflight-only validation over M1457 retarget candidates.

Decision:

```text
retargeted_source_step_preflight_pass_route_to_bounded_replay_design
```

M1459 ran only:

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
  --candidate-rows runs/m1457_source_step_boundary_retarget_smoke/retarget_candidate_rows.csv \
  --max-candidate-rows 128 \
  --per-capability-pair-cap 24 \
  --per-seed-cap 32 \
  --per-reveal-bucket-cap 16 \
  --per-variant-cap 64 \
  --history-length 56 \
  --min-sequence-action-l2 0.025 \
  --min-source-body-x 4.0 \
  --candidate-step-column source_step \
  --device cpu \
  --run-dir runs/m1459_retargeted_source_step_preflight_smoke
```

## Results

```text
candidate_step_column: source_step
input_rows: 128
history_candidate_rows: 128
geometry_pass_rows: 128
selected_candidate_rows: 104
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
max_single_seed_share: 0.269231
max_single_capability_pair_share: 0.153846
```

Geometry:

```text
source_body_x min / p50 / p95: 5.065734 / 9.589191 / 11.980351
```

Artifacts:

```text
runs/m1459_retargeted_source_step_preflight_smoke/summary.json
runs/m1459_retargeted_source_step_preflight_smoke/selected_candidate_rows.csv
runs/m1459_retargeted_source_step_preflight_smoke/geometry_preflight_rows.csv
```

## Interpretation

M1459 passes the retargeted source-step preflight gate. The M1457 retarget
candidate pool remains reconstructable, unclipped, source-diverse, and
`source_step` anchored.

This is still not replay evidence and does not prove history necessity. It only
admits a bounded replay smoke where terminal outcomes can be measured.

## Guardrails

M1459 guardrail status:

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
m1460-paper-route-retargeted-source-step-bounded-replay-design
```

M1460 should design a bounded replay smoke over the M1459 selected candidates
before any corpus export, actor update, PPO, or promotion.
