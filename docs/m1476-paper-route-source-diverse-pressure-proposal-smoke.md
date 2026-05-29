# M1476 Paper-Route Source-Diverse Pressure Proposal Smoke

## Summary

M1476 ran the source-diverse pressure generator from M1475 on M1472 artifacts.

Decision:

```text
source_diverse_pressure_proposal_smoke_pass_route_to_branch_synthesis
```

M1476 ran proposal generation only. It did not run preflight, replay, outcome
interventions, train, run PPO, promote, use private holdout, export corpus, or
change actor inputs.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.source_diverse_pressure \
  --actual-replay-rows runs/m1472_positive_neighborhood_bounded_replay_smoke/actual_replay_rows.csv \
  --history-positive-rows runs/m1472_positive_neighborhood_bounded_replay_smoke/history_positive_rows.csv \
  --control-positive-rows runs/m1472_positive_neighborhood_bounded_replay_smoke/control_positive_rows.csv \
  --candidate-pool runs/m1470_positive_neighborhood_preflight_smoke/selected_candidate_rows.csv \
  --max-candidates 192 \
  --per-seed-cap 24 \
  --per-capability-pair-cap 24 \
  --per-reveal-bucket-cap 24 \
  --per-relocation-key-cap 32 \
  --per-variant-cap 64 \
  --original-source-cap 12 \
  --control-diagnostic-cap 32 \
  --run-dir runs/m1476_source_diverse_pressure_proposal_smoke
```

## Results

```text
source_audit_rows: 213
pressure_candidate_source_rows: 63
proposal_rows: 1464
selected_candidate_rows: 120
selected_unique_pressure_keys: 120
selected_duplicate_pressure_key_rows: 0
candidate_step_column: source_step
```

Audit group counts:

```text
neighbor_source: 63
original_source: 8
control_diagnostic: 16
control_neighbor: 126
```

Proposal group counts:

```text
neighbor_source: 816
original_source: 216
control_diagnostic: 432
```

Selected group counts:

```text
neighbor_source: 96
original_source: 12
control_diagnostic: 12
```

Selected diversity:

```text
unique_source_seeds: 5
unique_capability_pairs: 7
unique_reveal_buckets: 7
unique_variants: 4
max_single_seed_share: 0.2
max_single_capability_pair_share: 0.2
```

## Interpretation

M1476 passes the proposal-level source-diversity gate. The generator did not
collapse back to the original source:

```text
neighbor_source selected rows: 96 / 120
unique source seeds: 5
unique capability pairs: 7
duplicate pressure keys: 0
```

This is not replay evidence. It only means a source-diverse candidate pool now
exists for the next validation step.

Because M1467-M1476 reaches the 10-milestone synthesis cadence after the M1466
reset, the next step should be branch synthesis before starting preflight or
replay.

## Guardrails

M1476 guardrail status:

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
m1477-paper-route-boundary-retarget-validation-synthesis
```
