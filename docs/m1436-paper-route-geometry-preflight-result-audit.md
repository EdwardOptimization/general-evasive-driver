# M1436 Paper-Route Geometry Preflight Result Audit

## Summary

M1436 audits M1435 before any threshold change, source mining, replay, or
training.

Decision:

```text
geometry_preflight_audit_pivot_to_forward_geometry_source_mining_design
```

M1436 does not run source preflight, replay, outcome interventions, training,
PPO, promotion, private holdout, corpus export, or actor-input changes.

## Classification

Classification:

```text
scenario_sampling_failure
source_pool_timing_failure
```

M1435 is not an implementation failure. The preflight-only command ran and
produced `846` preflight rows. The failure is source validity: every row in the
M1425 pressure pool is too close, behind, or clipped for forward-obstacle replay.

## Evidence

M1435 result:

```text
input_rows: 846
history_candidate_rows: 846
geometry_pass_rows: 0
selected_candidate_rows: 0
rejected_rows: 0
replay_started: false
training_started: false
actor_input_contract_changed: false
```

Rejection reasons:

```text
source_body_x_too_close|relocation_body_x_clipped: 789
source_body_x_too_close: 57
```

Source body-x:

```text
min: -3.508074
p50: -0.205025
p95: 3.812155
max: 3.908281
```

Raw relocated body-x:

```text
p50: -1.702453
p95: 2.162954
max: 3.495281
```

The important point is that `source_body_x max` is still below the
pre-registered `4.0m` forward gate, and the requested relocations often remain
behind or clipped.

## Supported Claims

Supported:

```text
1. the preflight-only command works and does not run replay;
2. M1425 pressure rows are not a valid forward/unclipped source pool;
3. M1429's geometry issue was not only top-128 selection bias;
4. source timing must be redesigned before bounded replay can be meaningful.
```

## Falsified Claims

Falsified or blocked:

```text
1. M1425 rows contain enough forward unclipped source geometry;
2. M1429 negative can be repaired by only changing top-k selection;
3. a bounded replay run should proceed from M1425 rows;
4. threshold lowering is justified by this result;
5. M1435 says anything about history necessity.
```

## Next Route

Pivot to design:

```text
m1437-paper-route-forward-geometry-source-mining-design
```

The next source design should search earlier or different source snapshots
before the obstacle has passed the ego vehicle. It should pre-register source
geometry before action divergence or replay:

```text
source_body_x >= 6.0 preferred
source_body_x_min >= 4.0 required
raw_relocated_body_x >= 4.0 required
relocation_body_x_clipped == false
unique_source_seeds >= 12 for source smoke
unique_capability_pairs >= 8
unique_history_variants >= 2
max_single_seed_share <= 0.25
```

The design should not lower the M1435 gates. It should change the source-mining
timing and scenario family so the rows are naturally forward and unclipped.

## Guardrails

M1436 guardrail status:

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
