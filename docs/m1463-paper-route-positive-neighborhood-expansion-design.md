# M1463 Paper-Route Positive Neighborhood Expansion Design

## Summary

M1463 designs the next no-training expansion around the live M1461
history-positive neighborhood.

Decision:

```text
positive_neighborhood_expansion_design_admit_implementation
```

M1463 does not run replay, train, run PPO, promote, use private holdout, export
corpus, or change actor inputs.

## Problem

M1461 found real history-positive replay rows:

```text
history_positive_rows: 2
seed: 141901
capability_pair: brake_authority_drop->mass_cg_shift
variant: warmup_removed
relocations:
  x=15.589|y=-0.790|w=0.908
  x=15.589|y=-0.790|w=1.108
```

But M1462 audited them as source-singleton and control-sensitive:

```text
history_positive_unique_source_seeds: 1
history_positive_unique_capability_pairs: 1
control_positive_rows: 8
```

So the next step is not corpus export or training. It is a candidate expansion
that tests whether this positive is a local surface or a singleton artifact.

## Expansion Design

Implement a no-training generator:

```text
src/autodrift/positive_neighborhood_expansion.py
```

Inputs:

```text
runs/m1461_retargeted_source_step_bounded_replay_smoke/history_positive_rows.csv
runs/m1461_retargeted_source_step_bounded_replay_smoke/control_positive_rows.csv
runs/m1461_retargeted_source_step_bounded_replay_smoke/actual_replay_rows.csv
runs/m1459_retargeted_source_step_preflight_smoke/selected_candidate_rows.csv
```

Outputs:

```text
positive_neighborhood_proposal_rows.csv
positive_neighborhood_candidate_rows.csv
summary.json
```

The generator should:

```text
1. Treat history-positive rows as anchors.
2. Keep zero-current control positives in a separate diagnostic table.
3. Build local body-frame grids around the anchor relocation.
4. Map source-diverse candidate bases from M1459 into that anchor neighborhood.
5. Preserve source_step and candidate_step_column == source_step.
6. Apply caps so one seed or pair cannot dominate the selected candidate pool.
```

## Candidate Construction

For each history-positive anchor, build target relocations:

```text
target_x = anchor_x + dx
target_y = anchor_y + dy
target_half_width = anchor_half_width + dw
```

Recommended grid:

```text
dx: -1.0, -0.5, 0.0, 0.5, 1.0, 2.0
dy: -0.4, -0.2, 0.0, 0.2, 0.4
dw: -0.1, 0.0, 0.1, 0.2
```

For any selected source base:

```text
body_longitudinal_offset = target_x - source_body_x
body_lateral_offset = target_y - source_body_y
half_width_inflation = target_half_width - source_half_width
```

This keeps the positive neighborhood fixed in ego/body geometry while allowing
different source seeds and capability pairs to test the same boundary region.

## Source Selection

Use three source groups:

```text
anchor_source:
  the original M1461 history-positive source.

control_source:
  rows from the same source family that produced zero-current control positives,
  kept as diagnostic candidates but not counted as history-positive evidence.

neighbor_sources:
  M1459 selected candidates with nearby source_step, source_body_x, source_body_y,
  and obstacle bucket, capped by seed and capability pair.
```

Selection priorities:

```text
1. anchor_source local grid, excluding exact duplicate-only replay if possible
2. neighbor_sources from different seeds and capability pairs
3. control_source diagnostics
```

Do not allow selected candidates to collapse back to one source:

```text
per_seed_cap <= 48
per_capability_pair_cap <= 32
per_anchor_cap <= 96
per_variant_cap <= 96
max_candidates <= 192
```

## Future Smoke Gate

The implementation should admit one proposal smoke only. That smoke should pass
if:

```text
proposal_rows >= 64
selected_candidate_rows >= 64
candidate_step_column == source_step
selected_diversity.unique_source_seeds >= 2 if available
selected_diversity.unique_capability_pairs >= 2 if available
history_positive_anchor_rows are reported separately
control_positive_source_rows are reported separately
source_preflight_started == false
replay_started == false
training_started == false
ppo_used == false
promoted == false
training_corpus_exported == false
actor_input_contract_changed == false
```

If the generator cannot build source-diverse candidates, route to branch
synthesis rather than replaying the singleton indefinitely.

## Guardrails

M1463 guardrail status:

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
m1464-paper-route-positive-neighborhood-expansion-implementation
```
