# M1469 Paper-Route Positive Neighborhood Preflight Design

## Summary

M1469 designs the preflight-only validation run over the deduplicated M1468
positive-neighborhood candidates.

Decision:

```text
positive_neighborhood_preflight_design_admit_smoke
```

M1469 does not run source preflight, bounded replay, outcome interventions,
training, PPO, promotion, private holdout, corpus export, or actor-input
changes.

## Preflight Objective

The preflight smoke should answer:

```text
Do deduplicated positive-neighborhood candidates remain forward, unclipped,
source-diverse, source_step anchored, and unique-key preserved when
reconstructed by the bounded relocation preflight tool?
```

Allowed claims:

```text
positive-neighborhood source-step preflight result
geometry pass / selected row counts
clipping and diversity diagnostics
unique-key retention diagnostic
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
runs/m1468_positive_neighborhood_dedup_smoke/positive_neighborhood_candidate_rows.csv
```

Preflight must use:

```text
--candidate-step-column source_step
```

## Smoke Command

Recommended preflight-only smoke:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.bounded_relocation_replay_probe \
  --preflight-only \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m1419_warmup_gate_invasiveness_retune_source_wave.json \
  --candidate-rows runs/m1468_positive_neighborhood_dedup_smoke/positive_neighborhood_candidate_rows.csv \
  --max-candidate-rows 192 \
  --per-capability-pair-cap 32 \
  --per-seed-cap 48 \
  --per-reveal-bucket-cap 24 \
  --per-variant-cap 96 \
  --history-length 56 \
  --min-sequence-action-l2 0.025 \
  --min-source-body-x 4.0 \
  --candidate-step-column source_step \
  --device cpu \
  --run-dir runs/m1470_positive_neighborhood_preflight_smoke
```

## Gate

M1470 should pass the preflight-run gate if:

```text
summary exists
candidate_step_column == source_step
geometry_pass_rows >= 64
selected_candidate_rows >= 64
selected_diversity.unique_source_seeds >= 2
selected_diversity.unique_capability_pairs >= 2
relocation_clipped_share <= 0.10
source_body_x_min >= 4.0
replay_started == false
training_started == false
ppo_used == false
promoted == false
private_holdout_used == false
training_corpus_exported == false
actor_input_contract_changed == false
```

The M1470 result document should also inspect:

```text
selected_candidate_rows.csv positive_neighborhood_key uniqueness
```

If M1470 passes, route to bounded replay design. If it fails, route to a
preflight result audit rather than lowering history standards.

## Guardrails

M1469 guardrail status:

```text
source_preflight_started: false
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
m1470-paper-route-positive-neighborhood-preflight-smoke
```
