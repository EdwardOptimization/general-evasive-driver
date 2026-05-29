# M1444 Paper-Route Geometry-Aware Preflight Validation Synthesis

## Summary

M1444 synthesizes the M1434-M1443 geometry-aware preflight validation branch
before continuing to row-level forward source mining.

Synthesis decision:

```text
promote_to_next_branch
```

Decision:

```text
geometry_aware_preflight_validation_synthesis_promote_to_forward_source_preflight_validation
```

M1444 does not run source preflight, bounded replay, outcome interventions,
training, PPO, promotion, private holdout, corpus export, or actor-input
changes.

## Evidence Summary

M1434 implemented a preflight-only command for bounded relocation replay. M1435
then ran it on the M1425 pressure-row pool and found:

```text
input_rows: 846
geometry_pass_rows: 0
selected_candidate_rows: 0
source_body_x_max: 3.908281
raw_relocated_body_x_max: 3.495281
```

M1436 audited this as a source-pool timing failure, not no-history evidence.
M1437-M1438 designed and implemented a row-level forward-geometry source miner,
but M1438 exposed that trace-backed source geometry materialization was still
missing.

M1439-M1440 designed and implemented trace-backed source geometry
materialization. M1441-M1442 designed and implemented source-step
action-divergence enrichment. M1443 then ran the public no-training source
pipeline:

```text
materialized source_geometry_rows: 320
materialization rejected_rows: 0
materialized unique seeds / pairs / buckets: 6 / 16 / 22
enriched_source_geometry_rows: 2880
selected_enriched_rows: 96
selected unique seeds / pairs / buckets / variants: 6 / 16 / 20 / 3
selected source_body_x min / p50 / max: 4.090512 / 9.310941 / 14.598930
selected sequence_action_l2_mean min / p50 / max: 0.071366 / 0.465744 / 0.725855
```

## Supported Claims

The branch supports these bounded claims:

```text
1. M1425 pressure rows were not a valid forward/unclipped source pool.
2. The failure was source timing, not evidence that history is unnecessary.
3. Trace-backed earlier source-step reconstruction can produce forward geometry.
4. Source-step action-divergent history rows exist after geometry-first filtering.
5. The selected M1443 rows are diverse enough for a row-level miner smoke.
6. No actor input, actor parameter, checkpoint, training, PPO, private holdout, or corpus-export shortcut was used.
```

## Falsified Claims

The branch falsifies or blocks these claims:

```text
1. M1425 reveal-step pressure rows should feed bounded replay directly.
2. Lowering source geometry gates is justified by M1435.
3. Source-step action divergence alone proves history necessity.
4. M1443 justifies training, corpus export, promotion, or paper-level self-ID claims.
5. The branch can continue without a synthesis decision after M1443.
```

## Failure Taxonomy Summary

Observed failure modes:

```text
scenario_sampling_failure_source_pool_timing_failure:
  M1435 showed M1425 rows were too late/near for forward geometry.

geometry_selector_failure:
  M1429/M1435 exposed clipped or too-close source geometry before trace-backed repair.

metric_artifact_risk:
  source-step action divergence is diagnostic only and must not be reported as outcome evidence.

public_row_overuse_risk:
  M1419/M1443 rows are public diagnostics and should not become training or paper holdout evidence.
```

## Public-Gate Overfit Risk

Risk level:

```text
medium
```

Reasons:

```text
M1419 source rows are public and have been inspected repeatedly;
source materialization/enrichment thresholds were designed after M1435 failure;
M1443 has only 6 selected unique seeds;
no bounded replay has validated terminal outcome sensitivity yet.
```

Mitigation:

```text
run only row-level miner and source preflight next;
do not train or export corpus from these rows;
do not claim self-ID until bounded replay shows outcome sensitivity;
if row-level miner or preflight fails, audit instead of lowering geometry gates.
```

## Next Branch Decision

Promote from:

```text
paper_route_geometry_aware_preflight_validation
```

to:

```text
paper_route_forward_source_preflight_validation
```

Admit:

```text
m1445-paper-route-forward-geometry-source-miner-smoke
```

M1445 should run the M1438 row-level forward geometry source miner on:

```text
runs/m1443_geometry_first_action_enrichment_smoke/selected_enriched_rows.csv
```

It must not run source preflight, bounded replay, outcome interventions,
training, PPO, promotion, private holdout, corpus export, or actor-input
changes.

## Guardrails

M1444 guardrail status:

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
