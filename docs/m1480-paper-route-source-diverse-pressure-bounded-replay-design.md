# M1480 Paper-Route Source-Diverse Pressure Bounded Replay Design

## Summary

M1480 designs bounded replay over M1479 source-diverse pressure preflight-pass
candidates.

Decision:

```text
source_diverse_pressure_bounded_replay_design_admit_smoke
```

M1480 does not run bounded replay, outcome interventions, training, PPO,
promotion, private holdout, corpus export, or actor-input changes.

## Replay Objective

The replay smoke should answer:

```text
Do M1479 source-diverse pressure candidates produce outcome-sensitive replay
rows, and if so, are any history positives source-diverse rather than the old
original-source singleton?
```

Allowed claims:

```text
bounded replay smoke result
actual replay row count
history-positive row count if observed
control-positive row count if observed
normal-failure count
source-group and diversity diagnostics
negative result requiring audit if no source-diverse history positives appear
```

Forbidden claims:

```text
training corpus quality
promotion readiness
paper-level self-identification
level3 anticipatory self-identification
private-holdout evidence
```

## Candidate Source

Use:

```text
runs/m1479_source_diverse_pressure_preflight_smoke/selected_candidate_rows.csv
```

Replay must use:

```text
--candidate-step-column source_step
```

## Smoke Command

Recommended bounded replay smoke:

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

## Gate

M1481 should pass the smoke-run gate if:

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

The M1481 result document should inspect:

```text
history_positive_rows
control_positive_rows
normal_failed_rows
history_positive source_group counts
history_positive source diversity
control_positive source diversity
actual_replay source diversity
```

If `history_positive_rows > 0`, route to replay result audit before any corpus
export. If `history_positive_rows == 0`, route to replay result audit rather
than weakening the self-identification standard.

## Guardrails

M1480 guardrail status:

```text
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
m1481-paper-route-source-diverse-pressure-bounded-replay-smoke
```
