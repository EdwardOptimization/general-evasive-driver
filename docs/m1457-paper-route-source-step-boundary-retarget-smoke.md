# M1457 Paper-Route Source-Step Boundary Retarget Smoke

## Summary

M1457 ran the source-step boundary retarget proposal generator implemented in
M1456 on the M1452 actual replay diagnostics.

Decision:

```text
source_step_boundary_retarget_smoke_pass_route_to_preflight_design
```

M1457 ran proposal generation only. It did not run source preflight, bounded
replay, outcome interventions, training, PPO, promotion, private holdout,
corpus export, or actor-input changes.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.source_step_replay_boundary_retarget \
  --actual-replay-rows runs/m1452_source_step_bounded_replay_smoke/actual_replay_rows.csv \
  --max-candidates 128 \
  --per-class-cap 64 \
  --per-seed-cap 32 \
  --per-capability-pair-cap 24 \
  --per-variant-cap 64 \
  --run-dir runs/m1457_source_step_boundary_retarget_smoke
```

## Results

```text
input_replay_rows: 192
history_variant_groups: 64
proposal_rows: 798
selected_retarget_rows: 128
candidate_step_column: source_step
```

Proposal class counts:

```text
normal_boundary: 90
too_easy: 228
too_hard: 480
```

Selected class counts:

```text
normal_boundary: 32
too_easy: 32
too_hard: 64
```

Selected diversity:

```text
unique_source_seeds: 5
unique_capability_pairs: 9
unique_reveal_buckets: 8
unique_variants: 3
max_single_seed_share: 0.25
max_single_capability_pair_share: 0.1875
```

Artifacts:

```text
runs/m1457_source_step_boundary_retarget_smoke/summary.json
runs/m1457_source_step_boundary_retarget_smoke/retarget_proposal_rows.csv
runs/m1457_source_step_boundary_retarget_smoke/retarget_candidate_rows.csv
```

## Interpretation

M1457 passes the proposal-generation gate. The selected retarget pool is large
enough, source-step anchored, and source-diverse enough to justify one
preflight-only validation design.

This result is not replay evidence and does not prove history necessity. It
only says the M1456 generator can construct a plausible retarget candidate pool
from M1452 diagnostics without lowering the evidence standard.

## Guardrails

M1457 guardrail status:

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
m1458-paper-route-retargeted-source-step-preflight-design
```

M1458 should design a preflight-only validation run over the M1457 retarget
candidates before any bounded replay, corpus export, actor update, PPO, or
promotion.
