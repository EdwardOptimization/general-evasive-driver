# M1479 Paper-Route Source-Diverse Pressure Preflight Smoke

## Summary

M1479 ran preflight-only validation over the M1476 source-diverse pressure
candidates.

Decision:

```text
source_diverse_pressure_preflight_pass_route_to_bounded_replay_design
```

M1479 ran source preflight only. It did not run bounded replay, outcome
interventions, train, run PPO, promote, use private holdout, export corpus, or
change actor inputs.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.bounded_relocation_replay_probe \
  --preflight-only \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m1419_warmup_gate_invasiveness_retune_source_wave.json \
  --candidate-rows runs/m1476_source_diverse_pressure_proposal_smoke/source_diverse_pressure_candidate_rows.csv \
  --max-candidate-rows 120 \
  --per-capability-pair-cap 24 \
  --per-seed-cap 24 \
  --per-reveal-bucket-cap 24 \
  --per-variant-cap 64 \
  --history-length 56 \
  --min-sequence-action-l2 0.025 \
  --min-source-body-x 4.0 \
  --candidate-step-column source_step \
  --device cpu \
  --run-dir runs/m1479_source_diverse_pressure_preflight_smoke
```

## Results

```text
input_rows: 108
geometry_pass_rows: 108
selected_candidate_rows: 108
rejected_rows: 0
relocation_clipped_share: 0.0
source_body_x_min: 5.157241
candidate_step_column: source_step
source_preflight_started: true
replay_started: false
```

Selected diversity:

```text
unique_source_seeds: 5
unique_capability_pairs: 7
unique_reveal_buckets: 7
unique_variants: 3
max_single_seed_share: 0.222222
max_single_capability_pair_share: 0.222222
```

Selected source groups:

```text
neighbor_source: 96
original_source: 12
control_diagnostic: 0
```

Duplicate and clipping diagnostics:

```text
unique_pressure_keys: 108
duplicate_pressure_key_rows: 0
relocation_body_x_clipped_rows: 0
relocation_half_width_clipped_rows: 0
```

## Interpretation

M1479 passes preflight. The source-diverse pressure candidates remain
source-step anchored, forward, unclipped, duplicate-key clean, and source
diverse after geometry reconstruction.

This is not replay evidence. It only admits a bounded replay design milestone.

## Guardrails

M1479 guardrail status:

```text
source_preflight_started: true
replay_started: false
outcome_interventions_started: false
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
m1480-paper-route-source-diverse-pressure-bounded-replay-design
```
