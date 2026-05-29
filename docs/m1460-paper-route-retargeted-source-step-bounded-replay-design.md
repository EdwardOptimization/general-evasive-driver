# M1460 Paper-Route Retargeted Source-Step Bounded Replay Design

## Summary

M1460 designs a bounded replay smoke over the M1459 retargeted source-step
preflight-pass candidates.

Decision:

```text
retargeted_source_step_bounded_replay_design_admit_smoke
```

M1460 does not run replay, train, run PPO, promote, use private holdout, export
corpus, or change actor inputs.

## Replay Objective

The replay smoke should answer:

```text
After boundary retargeting and source-step preflight validation, do any rows
produce terminal outcome sensitivity between normal history and selected history
interventions?
```

Allowed claims:

```text
bounded replay smoke result
history-positive row count if observed
control-positive row count if observed
normal-failure count
negative result requiring audit if no history-positive rows appear
```

Forbidden claims:

```text
training corpus quality
promotion readiness
paper-level self-identification
level3 anticipatory self-identification
generalization
private-holdout evidence
```

## Candidate Source

Use:

```text
runs/m1459_retargeted_source_step_preflight_smoke/selected_candidate_rows.csv
```

Replay must use:

```text
--candidate-step-column source_step
```

Do not use `reveal_step` for this replay route.

## Smoke Command

Recommended first replay smoke:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.bounded_relocation_replay_probe \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m1419_warmup_gate_invasiveness_retune_source_wave.json \
  --candidate-rows runs/m1459_retargeted_source_step_preflight_smoke/selected_candidate_rows.csv \
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
  --run-dir runs/m1461_retargeted_source_step_bounded_replay_smoke
```

## Gate

M1461 should pass the smoke-run gate if:

```text
summary exists
geometry_aware_selector == true
candidate_step_column == source_step
selected_candidate_rows >= 32
actual_replay_rows > 0
replay_started == true
training_started == false
ppo_used == false
promoted == false
private_holdout_used == false
training_corpus_exported == false
actor_input_contract_changed == false
```

If `history_positive_rows > 0`, route to replay result audit and compact corpus
design. If `history_positive_rows == 0`, route to replay result audit rather
than weakening history standards.

## Guardrails

M1460 guardrail status:

```text
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
m1461-paper-route-retargeted-source-step-bounded-replay-smoke
```
