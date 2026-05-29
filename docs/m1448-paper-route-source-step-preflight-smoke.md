# M1448 Paper-Route Source-Step Preflight Smoke

## Summary

M1448 attempted the pre-registered source-step preflight-only smoke on M1445
selected candidates.

Decision:

```text
source_step_preflight_schema_failure_route_to_margin_gap_optional_repair
```

Command failed before writing a run summary. No bounded replay, outcome
interventions, training, PPO, promotion, private holdout, corpus export, or
actor-input changes occurred.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.bounded_relocation_replay_probe \
  --preflight-only \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m1419_warmup_gate_invasiveness_retune_source_wave.json \
  --candidate-rows runs/m1445_forward_geometry_source_miner_smoke/selected_candidate_rows.csv \
  --max-candidate-rows 128 \
  --per-capability-pair-cap 12 \
  --per-seed-cap 24 \
  --per-reveal-bucket-cap 12 \
  --per-variant-cap 48 \
  --history-length 56 \
  --min-sequence-action-l2 0.025 \
  --min-source-body-x 4.0 \
  --candidate-step-column source_step \
  --device cpu \
  --run-dir runs/m1448_source_step_preflight_smoke
```

## Failure

Return code:

```text
1
```

Error:

```text
ValueError: candidate rows missing required columns: ['margin_gap']
```

M1445 `selected_candidate_rows.csv` is a source-step geometry/action-divergence
candidate pool. It contains `sequence_action_l2_mean`, source geometry,
relocation geometry, `source_step`, and diversity fields, but it does not carry
the outcome-pressure `margin_gap` field from older candidate rows.

## Interpretation

This is a schema compatibility failure, not a negative preflight result.

`margin_gap` is useful for ranking old outcome-pressure rows, but it is not
needed to reconstruct source-step geometry. For M1445-style rows it should be
optional and default to a neutral score:

```text
margin_gap = 0.0
```

The failure is classified as:

```text
lineage_invalid
```

because the M1445 candidate lineage is valid for source geometry but not yet
compatible with the old bounded relocation candidate schema.

## Guardrails

M1448 guardrail status:

```text
summary_written: false
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
m1449-paper-route-source-step-preflight-schema-repair-implementation
```

M1449 should make `margin_gap` optional in candidate preparation, default it to
`0.0` when absent, and add a focused regression test before rerunning preflight.
