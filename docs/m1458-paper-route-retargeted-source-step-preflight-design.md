# M1458 Paper-Route Retargeted Source-Step Preflight Design

## Summary

M1458 designs the preflight-only validation run admitted by the M1457 retarget
proposal smoke.

Decision:

```text
retargeted_source_step_preflight_design_admit_smoke
```

M1458 does not run source preflight, bounded replay, outcome interventions,
training, PPO, promotion, private holdout, corpus export, or actor-input
changes.

## Preflight Objective

The preflight smoke should answer:

```text
Do M1457 retarget candidates remain forward, unclipped, source-diverse, and
explicitly anchored at source_step when reconstructed by the bounded relocation
preflight tool?
```

Allowed claims:

```text
retargeted source-step preflight result
geometry pass / selected row counts
clipping and diversity diagnostics
negative result requiring audit if geometry or diversity fails
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
runs/m1457_source_step_boundary_retarget_smoke/retarget_candidate_rows.csv
```

Preflight must use:

```text
--candidate-step-column source_step
```

Do not use `reveal_step` for this retarget route.

## Smoke Command

Recommended preflight-only smoke:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.bounded_relocation_replay_probe \
  --preflight-only \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m1419_warmup_gate_invasiveness_retune_source_wave.json \
  --candidate-rows runs/m1457_source_step_boundary_retarget_smoke/retarget_candidate_rows.csv \
  --max-candidate-rows 128 \
  --per-capability-pair-cap 24 \
  --per-seed-cap 32 \
  --per-reveal-bucket-cap 16 \
  --per-variant-cap 64 \
  --history-length 56 \
  --min-sequence-action-l2 0.025 \
  --min-source-body-x 4.0 \
  --candidate-step-column source_step \
  --device cpu \
  --run-dir runs/m1459_retargeted_source_step_preflight_smoke
```

## Gate

M1459 should pass the preflight-run gate if:

```text
summary exists
candidate_step_column == source_step
geometry_pass_rows >= 64
selected_candidate_rows >= 64
selected_diversity.unique_source_seeds >= 4
selected_diversity.unique_capability_pairs >= 6
selected_diversity.unique_variants >= 2
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

If M1459 passes, route to a bounded replay design. If M1459 fails geometry or
diversity gates, route to a retarget preflight audit rather than lowering the
history standard.

## Guardrails

M1458 guardrail status:

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
m1459-paper-route-retargeted-source-step-preflight-smoke
```
