# M1485 Paper-Route Neighbor Viability Calibration Proposal Smoke

## Summary

M1485 ran the M1484 neighbor-viability calibration generator on the M1481
bounded replay artifacts.

Decision:

```text
neighbor_viability_calibration_proposal_smoke_pass_route_to_preflight_design
```

M1485 ran proposal generation only. It did not run source preflight, bounded
replay, outcome interventions, train, run PPO, promote, use private holdout,
export corpus, or change actor inputs.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.neighbor_viability_calibration \
  --actual-replay-rows runs/m1481_source_diverse_pressure_bounded_replay_smoke/actual_replay_rows.csv \
  --history-positive-rows runs/m1481_source_diverse_pressure_bounded_replay_smoke/history_positive_rows.csv \
  --control-positive-rows runs/m1481_source_diverse_pressure_bounded_replay_smoke/control_positive_rows.csv \
  --max-candidates 192 \
  --per-seed-cap 24 \
  --per-capability-pair-cap 24 \
  --per-reveal-bucket-cap 24 \
  --per-viability-class-cap 64 \
  --per-variant-cap 64 \
  --original-source-cap 8 \
  --control-diagnostic-cap 24 \
  --run-dir runs/m1485_neighbor_viability_calibration_proposal_smoke
```

## Results

```text
actual_replay_rows: 252
viability_audit_rows: 252
proposal_rows: 2208
calibration_candidate_rows: 72
selected_candidate_rows: 112
candidate_step_column: source_step
selected_duplicate_neighbor_viability_key_rows: 0
selected_unique_neighbor_viability_keys: 112
```

Selected source groups:

```text
neighbor_source: 88
original_source: 8
control_diagnostic: 16
```

Selected viability classes:

```text
too_hard: 64
near_boundary: 24
too_easy: 24
```

Selected diversity:

```text
unique_source_seeds: 5
unique_capability_pairs: 6
unique_reveal_buckets: 6
unique_variants: 4
max_single_seed_share: 0.214286
max_single_capability_pair_share: 0.214286
```

Audit source groups:

```text
neighbor_source: 72
original_source: 12
control_diagnostic: 24
control_neighbor: 144
```

Audit viability classes:

```text
too_hard: 150
near_boundary: 27
too_easy: 75
```

## Interpretation

M1485 passes the proposal-smoke criteria. It generated a nonempty calibrated
neighbor-source candidate set with source-step anchoring, source diversity, and
zero duplicate `neighbor_viability_key` rows.

This is not preflight or replay evidence. It only admits a preflight-design
milestone over the selected M1485 candidate rows.

## Guardrails

M1485 guardrail status:

```text
source_preflight_started: false
replay_started: false
outcome_interventions_started: false
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

Admit:

```text
m1486-paper-route-neighbor-viability-preflight-design
```
