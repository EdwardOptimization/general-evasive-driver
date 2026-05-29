# M1490 Paper-Route Neighbor Viability Bounded Replay Smoke

## Summary

M1490 ran the calibrated neighbor-viability bounded replay smoke over the M1487
preflight-pass candidates.

Decision:

```text
neighbor_viability_bounded_replay_positive_source_singleton_route_to_audit
```

Result class:

```text
bounded_relocation_replay_positive
```

M1490 ran bounded replay only. It did not train, run PPO, promote, use private
holdout, export corpus, or change actor inputs.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.bounded_relocation_replay_probe \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m1419_warmup_gate_invasiveness_retune_source_wave.json \
  --candidate-rows runs/m1487_neighbor_viability_preflight_smoke/selected_candidate_rows.csv \
  --geometry-aware-selector \
  --max-candidate-rows 96 \
  --per-capability-pair-cap 16 \
  --per-seed-cap 24 \
  --per-reveal-bucket-cap 12 \
  --per-variant-cap 48 \
  --history-length 56 \
  --recent-window-length 4 \
  --max-continuation-steps 48 \
  --min-margin-gap 0.02 \
  --min-sequence-action-l2 0.025 \
  --min-source-body-x 4.0 \
  --candidate-step-column source_step \
  --device cpu \
  --run-dir runs/m1490_neighbor_viability_bounded_replay_smoke
```

## Results

```text
selected_candidate_rows: 68
actual_replay_rows: 204
history_positive_rows: 7
control_positive_rows: 12
normal_failed_rows: 147
candidate_step_column: source_step
geometry_aware_selector: true
```

Actual replay diversity:

```text
unique_source_seeds: 5
unique_capability_pairs: 6
unique_reveal_buckets: 6
unique_variants: 5
max_single_seed_share: 0.352941
max_single_capability_pair_share: 0.176471
```

History-positive diversity:

```text
unique_source_seeds: 1
unique_capability_pairs: 1
unique_reveal_buckets: 1
unique_variants: 1
max_single_seed_share: 1.0
max_single_capability_pair_share: 1.0
```

History-positive family:

```text
seed: 141901
capability_pair: brake_authority_drop->mass_cg_shift
reveal_bucket: vx6|yaw-2|steer-4|ox0|oy0
variant: warmup_removed
```

Control-positive diversity:

```text
control_positive_rows: 12
unique_source_seeds: 1
unique_capability_pairs: 1
variants: reset_hidden, zero_current_response
```

Selected candidate source groups:

```text
neighbor_source: 60
original_source: 8
```

Selected candidate viability classes:

```text
too_hard: 36
too_easy: 24
near_boundary: 8
```

## Interpretation

M1490 is a replay-positive smoke, but it does not solve the source-diverse
history-positive blocker. Actual replay was source-diverse, yet all
history-positive rows remained source-singleton, and control positives were
also concentrated on the same family.

This strengthens the M1488 hard-stop condition. The result should be audited as
a replay-positive but source-singleton/control-sensitive outcome. It should not
be exported as a corpus and should not trigger training, PPO, promotion, or
level3 self-ID claims.

## Guardrails

M1490 guardrail status:

```text
replay_started: true
training_started: false
evaluation_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_input_contract_changed: false
level3_self_id_claim_made: false
```

## Next Route

Admit mandatory audit:

```text
m1491-paper-route-neighbor-viability-replay-result-audit
```
