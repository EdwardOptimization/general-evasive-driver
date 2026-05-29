# M1478 Paper-Route Source-Diverse Pressure Preflight Design

## Summary

M1478 designs the preflight-only validation run for M1476 source-diverse
pressure candidates.

Decision:

```text
source_diverse_pressure_preflight_design_admit_smoke
```

M1478 does not run source preflight, bounded replay, outcome interventions,
training, PPO, promotion, private holdout, corpus export, or actor-input
changes.

## Preflight Objective

The preflight smoke should answer:

```text
Do M1476 source-diverse pressure candidates remain forward, unclipped,
source-diverse, source_step anchored, and duplicate-key clean when reconstructed
by the bounded relocation preflight tool?
```

Allowed claims:

```text
source-diverse pressure preflight result
geometry pass / selected row counts
clipping and diversity diagnostics
source_group retention diagnostic
duplicate pressure-key diagnostic
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
runs/m1476_source_diverse_pressure_proposal_smoke/source_diverse_pressure_candidate_rows.csv
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

## Gate

M1479 should pass the preflight-run gate if:

```text
summary exists
candidate_step_column == source_step
geometry_pass_rows >= 64
selected_candidate_rows >= 64
selected_diversity.unique_source_seeds >= 3
selected_diversity.unique_capability_pairs >= 4
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
selected_candidate_rows.csv source_diverse_pressure_key uniqueness
```

If M1479 passes, route to bounded replay design. If it fails, route to preflight
result audit rather than lowering history standards.

## Guardrails

M1478 guardrail status:

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
m1479-paper-route-source-diverse-pressure-preflight-smoke
```
