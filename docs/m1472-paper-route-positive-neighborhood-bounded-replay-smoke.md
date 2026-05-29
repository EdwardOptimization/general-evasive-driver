# M1472 Paper-Route Positive Neighborhood Bounded Replay Smoke

## Summary

M1472 ran bounded replay over M1470 positive-neighborhood preflight-pass
candidates.

Decision:

```text
positive_neighborhood_bounded_replay_positive_local_surface_route_to_audit
```

M1472 ran bounded replay only. It did not train, run PPO, promote, use private
holdout, export corpus, or change actor inputs.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.bounded_relocation_replay_probe \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m1419_warmup_gate_invasiveness_retune_source_wave.json \
  --candidate-rows runs/m1470_positive_neighborhood_preflight_smoke/selected_candidate_rows.csv \
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
  --run-dir runs/m1472_positive_neighborhood_bounded_replay_smoke
```

## Results

```text
candidate_step_column: source_step
geometry_aware_selector: true
selected_candidate_rows: 96
actual_replay_rows: 288
history_positive_rows: 8
control_positive_rows: 12
normal_failed_rows: 108
result_class: bounded_relocation_replay_positive
```

Replay diversity:

```text
unique_source_seeds: 5
unique_capability_pairs: 8
unique_reveal_buckets: 8
unique_variants: 5
max_single_seed_share: 0.25
max_single_capability_pair_share: 0.125
```

History-positive diversity:

```text
rows: 8
unique_source_seeds: 1
unique_capability_pairs: 1
unique_reveal_buckets: 1
unique_variants: 1
unique_relocation_keys: 7
```

Control-positive diversity:

```text
rows: 12
unique_source_seeds: 1
unique_capability_pairs: 1
unique_reveal_buckets: 1
unique_variants: 1
```

Variant summary:

```text
warmup_removed: 36 rows, 8 history positives
zero_current_response: 96 rows, 12 control positives
reset_hidden: 96 rows, 0 positives
warmup_shortened_8: 36 rows, 0 positives
delayed_warmup_history_16: 24 rows, 0 positives
```

Margins and action distances:

```text
normal_margin min / p50 / max: 0.474946 / 2.520921 / 8.493331
variant_margin min / p50 / max: 0.400177 / 2.571940 / 8.493607
margin_gap min / p50 / max: -0.166477 / -0.027659 / 0.093845
sequence_action_l2_mean min / p50 / max: 0.041742 / 0.272617 / 0.624832
```

## Interpretation

M1472 expands the M1461 singleton from:

```text
2 history-positive rows, 2 relocation keys
```

to:

```text
8 history-positive rows, 7 relocation keys
```

So the positive-neighborhood expansion did find a local outcome-sensitive
surface.

It still did not produce source-diverse history positives. All history-positive
rows remain on the original seed / capability pair / reveal bucket / variant.
This blocks corpus export, training, promotion, and paper-level claims.

## Guardrails

M1472 guardrail status:

```text
replay_started: true
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
m1473-paper-route-positive-neighborhood-replay-result-audit
```
