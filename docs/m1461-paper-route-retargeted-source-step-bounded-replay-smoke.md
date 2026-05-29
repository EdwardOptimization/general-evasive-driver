# M1461 Paper-Route Retargeted Source-Step Bounded Replay Smoke

## Summary

M1461 ran the bounded replay smoke over M1459 retargeted source-step
preflight-pass candidates.

Decision:

```text
retargeted_source_step_bounded_replay_positive_route_to_audit
```

M1461 ran bounded replay only. It did not train, run PPO, promote, use private
holdout, export corpus, or change actor inputs.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.bounded_relocation_replay_probe \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m1419_warmup_gate_invasiveness_retune_source_wave.json \
  --candidate-rows runs/m1459_retargeted_source_step_preflight_smoke/selected_candidate_rows.csv \
  --geometry-aware-selector \
  --max-candidate-rows 64 \
  --per-capability-pair-cap 8 \
  --per-seed-cap 12 \
  --per-reveal-bucket-cap 8 \
  --per-variant-cap 24 \
  --history-length 56 \
  --recent-window-length 4 \
  --max-continuation-steps 48 \
  --min-margin-gap 0.02 \
  --min-sequence-action-l2 0.025 \
  --min-source-body-x 4.0 \
  --candidate-step-column source_step \
  --device cpu \
  --run-dir runs/m1461_retargeted_source_step_bounded_replay_smoke
```

## Results

```text
candidate_step_column: source_step
geometry_aware_selector: true
selected_candidate_rows: 52
actual_replay_rows: 156
history_positive_rows: 2
control_positive_rows: 8
normal_failed_rows: 78
result_class: bounded_relocation_replay_positive
```

Replay diversity:

```text
unique_source_seeds: 5
unique_capability_pairs: 8
unique_reveal_buckets: 8
unique_variants: 5
max_single_seed_share: 0.230769
max_single_capability_pair_share: 0.153846
```

History-positive diversity:

```text
rows: 2
unique_source_seeds: 1
unique_capability_pairs: 1
unique_reveal_buckets: 1
unique_variants: 1
```

Control-positive diversity:

```text
rows: 8
unique_source_seeds: 1
unique_capability_pairs: 1
unique_reveal_buckets: 1
unique_variants: 1
```

Variant summary:

```text
warmup_removed: 20 rows, 2 history positives
zero_current_response: 52 rows, 8 control positives
reset_hidden: 52 rows, 0 positives
warmup_shortened_8: 20 rows, 0 positives
delayed_warmup_history_16: 12 rows, 0 positives
```

Margins and action distances:

```text
normal_margin min / p50 / max: -0.201199 / 2.496107 / 5.827906
variant_margin min / p50 / max: -0.179474 / 2.497255 / 5.827745
margin_gap min / p50 / max: -0.217759 / -0.003396 / 0.075780
sequence_action_l2_mean min / p50 / max: 0.041742 / 0.249611 / 0.619808
```

History-positive rows:

```text
seed: 141901
candidate_step: 24
capability_pair: brake_authority_drop->mass_cg_shift
bucket: vx6|yaw-2|steer-4|ox0|oy0
variant: warmup_removed
relocation: x=15.589|y=-0.790|w=0.908, margin_gap=0.030644
relocation: x=15.589|y=-0.790|w=1.108, margin_gap=0.030101
```

## Interpretation

M1461 is the first retargeted source-step replay smoke on this branch to find
history-positive rows. Boundary retargeting therefore found a live
outcome-sensitive neighborhood that M1452 missed.

This is still not enough for corpus export, training, promotion, paper-level
self-identification, or a level3 claim. The positives are source-singleton and
the same source also produces zero-current control positives. The immediate
next step is an audit and a source-diverse positive-neighborhood expansion
design.

## Guardrails

M1461 guardrail status:

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
m1462-paper-route-retargeted-bounded-replay-result-audit
```
