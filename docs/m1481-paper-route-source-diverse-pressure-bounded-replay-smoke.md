# M1481 Paper-Route Source-Diverse Pressure Bounded Replay Smoke

## Summary

M1481 ran bounded replay over M1479 source-diverse pressure preflight-pass
candidates.

Decision:

```text
source_diverse_pressure_bounded_replay_positive_source_singleton_route_to_audit
```

M1481 ran bounded replay only. It did not train, run PPO, promote, use private
holdout, export corpus, or change actor inputs.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.bounded_relocation_replay_probe \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m1419_warmup_gate_invasiveness_retune_source_wave.json \
  --candidate-rows runs/m1479_source_diverse_pressure_preflight_smoke/selected_candidate_rows.csv \
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
  --run-dir runs/m1481_source_diverse_pressure_bounded_replay_smoke
```

## Results

```text
candidate_step_column: source_step
geometry_aware_selector: true
selected_candidate_rows: 84
actual_replay_rows: 252
history_positive_rows: 12
control_positive_rows: 15
normal_failed_rows: 150
result_class: bounded_relocation_replay_positive
```

Actual replay diversity:

```text
unique_source_seeds: 5
unique_capability_pairs: 7
unique_reveal_buckets: 7
unique_variants: 5
max_single_seed_share: 0.285714
max_single_capability_pair_share: 0.142857
```

History-positive diversity:

```text
rows: 12
unique_source_seeds: 1
unique_capability_pairs: 1
unique_reveal_buckets: 1
unique_variants: 1
seed: 141901
capability_pair: brake_authority_drop->mass_cg_shift
variant: warmup_removed
```

Control-positive diversity:

```text
rows: 15
unique_source_seeds: 1
unique_capability_pairs: 1
unique_reveal_buckets: 1
unique_variants: 2
seed: 141901
capability_pair: brake_authority_drop->mass_cg_shift
variants: zero_current_response, reset_hidden
```

Margin diagnostics:

```text
history_positive margin_gap min / p50 / max: 0.030101 / 0.086028 / 0.184710
history_positive normal_margin min / p50 / max: 0.197008 / 0.426433 / 0.876342
control_positive margin_gap min / p50 / max: 0.040575 / 0.087893 / 0.126964
control_positive normal_margin min / p50 / max: 0.197008 / 0.454985 / 0.876342
```

## Interpretation

M1481 is a replay-positive result, but it does not solve the source-diversity
blocker.

The candidate pool and actual replay are source-diverse, but all
history-positive rows collapse back to the original source family. The same
source family also produces control positives. Therefore:

```text
supported: source-diverse pressure candidates can be replayed and produce local positives
unsupported: source-diverse history-positive replay evidence exists
unsupported: training corpus export is ready
unsupported: paper-level self-identification evidence is ready
```

This must route to audit before any corpus export, training, or further pressure
generation.

## Guardrails

M1481 guardrail status:

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
m1482-paper-route-source-diverse-pressure-replay-result-audit
```
