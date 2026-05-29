# M1487 Paper-Route Neighbor Viability Preflight Smoke

## Summary

M1487 ran preflight-only validation over the M1485 calibrated
neighbor-viability candidates.

Decision:

```text
neighbor_viability_preflight_pass_route_to_branch_synthesis
```

M1487 ran only source preflight. It did not run bounded replay, outcome
interventions, train, run PPO, promote, use private holdout, export corpus, or
change actor inputs.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.bounded_relocation_replay_probe \
  --preflight-only \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m1419_warmup_gate_invasiveness_retune_source_wave.json \
  --candidate-rows runs/m1485_neighbor_viability_calibration_proposal_smoke/neighbor_viability_candidate_rows.csv \
  --max-candidate-rows 112 \
  --per-capability-pair-cap 24 \
  --per-seed-cap 24 \
  --per-reveal-bucket-cap 24 \
  --per-variant-cap 64 \
  --history-length 56 \
  --min-sequence-action-l2 0.025 \
  --min-source-body-x 4.0 \
  --candidate-step-column source_step \
  --device cpu \
  --run-dir runs/m1487_neighbor_viability_preflight_smoke
```

## Results

```text
input_rows: 96
geometry_pass_rows: 96
selected_candidate_rows: 96
rejected_rows: 0
relocation_clipped_share: 0.0
source_body_x_min: 5.157241
source_body_x_p50: 10.361459
source_body_x_p95: 11.980351
candidate_step_column: source_step
```

Selected diversity:

```text
unique_source_seeds: 5
unique_capability_pairs: 6
unique_reveal_buckets: 6
unique_variants: 3
max_single_seed_share: 0.25
max_single_capability_pair_share: 0.25
```

Selected source groups:

```text
neighbor_source: 88
original_source: 8
control_diagnostic: 0
```

Selected viability classes:

```text
too_hard: 64
too_easy: 24
near_boundary: 8
```

Duplicate-key diagnostics:

```text
selected_unique_neighbor_viability_keys: 96
selected_duplicate_neighbor_viability_key_rows: 0
```

## Interpretation

M1487 passes the preflight gate. The M1485 calibrated candidates remain
forward, unclipped, source-step anchored, source-diverse, and duplicate-key
clean after geometry reconstruction.

This is not replay evidence. It does not prove history-positive outcome rows,
source-diverse self-identification, training corpus quality, or promotion
readiness.

Because the source-diverse pressure validation branch has now run another
proposal -> design -> preflight sequence after M1477, the next step should be a
branch synthesis before any replay design. The synthesis should incorporate the
new self-ID go/no-go paper-route plan and decide whether calibrated replay is
still the highest-leverage next experiment.

## Guardrails

M1487 guardrail status:

```text
source_preflight_started: true
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
m1488-paper-route-source-diverse-pressure-validation-synthesis
```
