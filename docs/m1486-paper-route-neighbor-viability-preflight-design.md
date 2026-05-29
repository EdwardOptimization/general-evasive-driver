# M1486 Paper-Route Neighbor Viability Preflight Design

## Summary

M1486 designs the preflight-only validation run for the M1485 calibrated
neighbor-viability candidates.

Decision:

```text
neighbor_viability_preflight_design_admit_smoke
```

M1486 does not run source preflight, bounded replay, outcome interventions,
training, PPO, promotion, private holdout, corpus export, or actor-input
changes.

## Preflight Objective

The M1487 preflight smoke should answer:

```text
Do M1485 calibrated neighbor-viability candidates remain forward, unclipped,
source-diverse, source_step anchored, and duplicate-key clean when reconstructed
by the bounded relocation preflight tool?
```

Allowed claims:

```text
neighbor viability preflight result
geometry pass / selected row counts
clipping and diversity diagnostics
source_group retention diagnostic
viability_class retention diagnostic
duplicate neighbor_viability_key diagnostic
negative result requiring audit if geometry, diversity, or uniqueness fails
```

Forbidden claims:

```text
bounded replay evidence
history-positive evidence
training corpus quality
promotion readiness
paper-level self-identification
level3 anticipatory self-identification
private-holdout evidence
```

## Candidate Source

Use:

```text
runs/m1485_neighbor_viability_calibration_proposal_smoke/neighbor_viability_candidate_rows.csv
```

Preflight must use:

```text
--candidate-step-column source_step
```

M1485 selected:

```text
selected_candidate_rows: 112
neighbor_source: 88
original_source: 8
control_diagnostic: 16
unique_source_seeds: 5
unique_capability_pairs: 6
unique_reveal_buckets: 6
unique_variants: 4
duplicate neighbor_viability_key rows: 0
```

## Smoke Command

Recommended preflight-only smoke:

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

## Gate

M1487 should pass the preflight-run gate if:

```text
summary exists
candidate_step_column == source_step
geometry_pass_rows >= 64
selected_candidate_rows >= 64
selected_diversity.unique_source_seeds >= 3
selected_diversity.unique_capability_pairs >= 4
selected_diversity.unique_reveal_buckets >= 3
relocation_clipped_share <= 0.10
source_body_x_min >= 4.0
source_preflight_started == true
replay_started == false
training_started == false
ppo_used == false
promoted == false
private_holdout_used == false
training_corpus_exported == false
actor_input_contract_changed == false
```

The result document should also inspect:

```text
selected_candidate_rows.csv source_group counts
selected_candidate_rows.csv viability_class counts
selected_candidate_rows.csv neighbor_viability_key uniqueness
selected_candidate_rows.csv calibration_candidate counts
```

If M1487 passes, route to branch synthesis before any replay design. This keeps
the current source-diverse pressure validation branch within the workflow
synthesis cadence and lets the next decision incorporate the new self-ID
go/no-go paper-route plan.

If M1487 fails, route to a preflight result audit rather than lowering history
standards or replaying unvalidated candidates.

## Guardrails

M1486 guardrail status:

```text
source_preflight_started: false
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
m1487-paper-route-neighbor-viability-preflight-smoke
```
