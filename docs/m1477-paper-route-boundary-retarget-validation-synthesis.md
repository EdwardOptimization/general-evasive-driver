# M1477 Paper-Route Boundary Retarget Validation Synthesis

## Summary

M1477 synthesizes M1467-M1476 after the M1466 branch reset.

Decision:

```text
boundary_retarget_validation_synthesis_promote_to_source_diverse_pressure_validation
```

Synthesis decision:

```text
promote_to_next_branch
```

Closed branch:

```text
paper_route_source_step_boundary_retarget_validation
```

New branch:

```text
paper_route_source_diverse_pressure_validation
```

M1477 does not run preflight, replay, outcome interventions, train, run PPO,
promote a checkpoint, use private holdout, export corpus, or change actor
inputs.

## Evidence Summary

The branch after M1466 had one job:

```text
repair the duplicate-key artifact and decide whether the live M1461/M1472 local
positive surface can be converted into source-diverse validation pressure.
```

Milestone path:

```text
M1467: repaired positive-neighborhood duplicate-key selection.
M1468: proposal smoke produced 192 selected candidates with 192 unique keys.
M1469: designed positive-neighborhood preflight.
M1470: preflight passed with 171 selected rows and source-step anchoring.
M1471: designed positive-neighborhood bounded replay.
M1472: bounded replay found 8 history positives across 7 relocation keys.
M1473: audited M1472 as local-surface positive but source-singleton.
M1474: designed source-diverse pressure route.
M1475: implemented source-diverse pressure generator.
M1476: proposal smoke selected 120 source-diverse pressure candidates.
```

Key M1476 result:

```text
source_audit_rows: 213
pressure_candidate_source_rows: 63
proposal_rows: 1464
selected_candidate_rows: 120
selected_source_group_counts: 96 neighbor_source / 12 original_source / 12 control_diagnostic
selected diversity: 5 seeds / 7 capability pairs / 7 reveal buckets / 4 variants
duplicate pressure keys: 0
```

## Supported Claims

Supported:

```text
The source-step boundary retarget path is now mechanically clean enough to
produce source-step anchored, duplicate-free candidate pools.

M1472 proves the positive-neighborhood surface is not a pure singleton artifact:
it expanded from 2 history-positive rows to 8 history-positive rows across 7
relocation keys.

M1476 proves source-diverse pressure candidates can be generated from that local
surface without replay, training, corpus export, or actor-input changes.
```

## Falsified Or Unsupported Claims

Unsupported:

```text
M1472 positives are source-diverse replay evidence.

M1472 positives are ready for training corpus export.

M1476 proposal counts are replay evidence.

M1476 proposal counts are paper-level self-identification evidence.

Any level3 anticipatory self-identification claim.
```

Falsified for this branch:

```text
Simple local positive-neighborhood expansion alone is enough to produce
source-diverse replay positives.
```

## Failure Taxonomy Summary

```text
metric_artifact:
  M1465 selected rows were inflated by duplicate positive-neighborhood keys.
  M1467/M1468 repaired this.

scenario_sampling_failure:
  M1472 replay positives remained one source family and were control-sensitive.
  M1473 blocked corpus export and routed to source-diverse pressure.

none:
  M1475 implementation and M1476 proposal generation passed their infrastructure
  gates.
```

No contract violation was observed. The actor input contract remains unchanged.

## Public Gate Overfit Risk

Risk:

```text
medium_high
```

Reason:

```text
M1476 source diversity is proposal-level and derived from public M1472/M1470
artifacts. It is useful enough to justify preflight, but not enough for replay,
corpus, training, promotion, private-holdout, or paper-level claims.
```

## Next Branch Decision

Promote to a new validation branch:

```text
paper_route_source_diverse_pressure_validation
```

The next branch should test the M1476 candidate pool in stages:

```text
1. source-diverse pressure preflight design
2. source-diverse pressure preflight smoke
3. preflight result audit
4. bounded replay design only if preflight passes
5. bounded replay smoke only after design
6. replay result audit before any corpus export or training
```

The branch must keep zero-current controls separate and must not claim
history-necessity until source-diverse replay positives exist.

## Guardrails

M1477 guardrail status:

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
m1478-paper-route-source-diverse-pressure-preflight-design
```
