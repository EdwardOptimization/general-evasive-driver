# M1489 Paper-Route Neighbor Viability Bounded Replay Design

## Summary

M1489 designs one calibrated bounded replay smoke over the M1487 preflight-pass
neighbor-viability candidates.

Decision:

```text
neighbor_viability_bounded_replay_design_admit_smoke
```

M1489 does not run bounded replay, outcome interventions, training, PPO,
promotion, private holdout, corpus export, or actor-input changes.

## Replay Objective

The M1490 replay smoke should answer:

```text
Does M1485/M1487 neighbor viability calibration transfer from geometry-valid
source-step candidates to outcome-sensitive replay rows, and if so, are any
history positives source-diverse rather than another original-source singleton?
```

Allowed claims:

```text
bounded replay smoke result
actual replay row count
history-positive row count if observed
control-positive row count if observed
normal-failure count
source-group, viability-class, and diversity diagnostics
negative result requiring audit if no source-diverse history positives appear
```

Forbidden claims:

```text
training corpus quality
promotion readiness
paper-level self-identification
level3 anticipatory self-identification
private-holdout evidence
GRU recurrent-belief advantage
```

## Candidate Source

Use:

```text
runs/m1487_neighbor_viability_preflight_smoke/selected_candidate_rows.csv
```

Replay must use:

```text
--geometry-aware-selector
--candidate-step-column source_step
```

M1487 selected:

```text
selected_candidate_rows: 96
neighbor_source: 88
original_source: 8
unique_source_seeds: 5
unique_capability_pairs: 6
unique_reveal_buckets: 6
unique_variants: 3
duplicate neighbor_viability_key rows: 0
relocation_clipped_share: 0.0
```

## Smoke Command

Recommended bounded replay smoke:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.bounded_relocation_replay_probe \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m1419_warmup_gate_invasiveness_retune_source_wave.json \
  --candidate-rows runs/m1487_neighbor_viability_preflight_smoke/selected_candidate_rows.csv \
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
  --run-dir runs/m1490_neighbor_viability_bounded_replay_smoke
```

## Gate

M1490 should pass the smoke-run gate if:

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

The M1490 result document should inspect:

```text
history_positive_rows
control_positive_rows
normal_failed_rows
actual_replay source diversity
history_positive source diversity
control_positive source diversity
history_positive source_group counts
history_positive viability_class counts
control_positive source_group counts
control_positive viability_class counts
neighbor-source versus original-source positives
```

If `history_positive_rows > 0`, route to replay result audit before any corpus
export. If `history_positive_rows == 0`, also route to replay result audit
rather than weakening the self-identification standard.

The M1491 audit must apply the M1488 hard stop:

```text
If replay positives remain source-singleton or control-explained, stop this
source-diverse pressure loop and pivot to the L0/L1/L2/L3 go/no-go matrix.
```

## Guardrails

M1489 guardrail status:

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
m1490-paper-route-neighbor-viability-bounded-replay-smoke
```
