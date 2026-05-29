# M1452 Paper-Route Source-Step Bounded Replay Smoke

## Summary

M1452 ran the first source-step bounded replay smoke on M1450 preflight-pass
candidates.

Decision:

```text
source_step_bounded_replay_no_history_positive_route_to_audit
```

M1452 ran bounded replay only. It did not train, run PPO, promote, use private
holdout, export corpus, or change actor inputs.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.bounded_relocation_replay_probe \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m1419_warmup_gate_invasiveness_retune_source_wave.json \
  --candidate-rows runs/m1450_source_step_preflight_rerun/selected_candidate_rows.csv \
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
  --run-dir runs/m1452_source_step_bounded_replay_smoke
```

## Results

```text
candidate_step_column: source_step
geometry_aware_selector: true
selected_candidate_rows: 64
actual_replay_rows: 192
history_positive_rows: 0
control_positive_rows: 0
normal_failed_rows: 120
result_class: bounded_relocation_replay_no_history_positive
```

Replay diversity:

```text
unique_source_seeds: 6
unique_capability_pairs: 11
unique_reveal_buckets: 12
unique_variants: 5
max_single_seed_share: 0.1875
max_single_capability_pair_share: 0.125
```

Variant summary:

```text
delayed_warmup_history_16: 24 rows, 0 positives
warmup_removed: 24 rows, 0 positives
warmup_shortened_8: 16 rows, 0 positives
reset_hidden: 64 rows, 0 positives
zero_current_response: 64 rows, 0 positives
```

Margins and action distances:

```text
normal_margin min / p50 / max: -0.261073 / 1.197823 / 5.494914
variant_margin min / p50 / max: -0.260751 / 1.262268 / 5.511063
margin_gap min / p50 / max: -0.716577 / -0.018147 / 0.230136
sequence_action_l2_mean min / p50 / max: 0.043760 / 0.281583 / 0.637304
```

## Interpretation

M1452 proves the source-step replay route is runnable and records actual replay
rows. It does not find history-positive rows.

This is not evidence that history is unnecessary. The replay distribution is
not yet outcome-boundary aligned:

```text
120 / 192 replay rows have normal failure or negative normal margin.
72 / 192 rows are normal-success rows, but variants do not create accepted
success drops or margin gaps.
```

The likely failure mode is replay pressure placement:

```text
too many rows are already infeasible under normal history;
the remaining rows are not near the terminal margin boundary.
```

Action divergence exists, but terminal outcome sensitivity does not appear in
this replay smoke.

## Guardrails

M1452 guardrail status:

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
m1453-paper-route-source-step-bounded-replay-result-audit
```

The audit should classify this as a replay pressure / boundary-targeting issue
before any threshold changes, corpus export, training, or PPO.
