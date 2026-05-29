# M1471 Paper-Route Positive Neighborhood Bounded Replay Design

## Summary

M1471 designs a bounded replay smoke over the M1470 positive-neighborhood
preflight-pass candidates.

Decision:

```text
positive_neighborhood_bounded_replay_design_admit_smoke
```

M1471 does not run replay, train, run PPO, promote, use private holdout, export
corpus, or change actor inputs.

## Replay Objective

The replay smoke should answer:

```text
After dedup repair and preflight validation, does the positive-neighborhood
surface produce history-positive outcome rows beyond the original singleton?
```

Allowed claims:

```text
bounded replay smoke result
history-positive row count if observed
control-positive row count if observed
normal-failure count
unique-key retention diagnostic
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
runs/m1470_positive_neighborhood_preflight_smoke/selected_candidate_rows.csv
```

Replay must use:

```text
--candidate-step-column source_step
```

## Smoke Command

Recommended first replay smoke:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.bounded_relocation_replay_probe \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m1419_warmup_gate_invasiveness_retune_source_wave.json \
  --candidate-rows runs/m1470_positive_neighborhood_preflight_smoke/selected_candidate_rows.csv \
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
  --run-dir runs/m1472_positive_neighborhood_bounded_replay_smoke
```

## Gate

M1472 should pass the smoke-run gate if:

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

The M1472 result document should also inspect:

```text
actual_replay_rows.csv positive_neighborhood_key uniqueness and diversity
```

If `history_positive_rows > 0`, route to replay result audit and compact
surface design. If `history_positive_rows == 0`, route to replay result audit
rather than weakening history standards.

## Guardrails

M1471 guardrail status:

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
m1472-paper-route-positive-neighborhood-bounded-replay-smoke
```
