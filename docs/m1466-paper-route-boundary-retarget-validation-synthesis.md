# M1466 Paper-Route Boundary Retarget Validation Synthesis

## Summary

M1466 synthesizes the `paper_route_source_step_boundary_retarget_validation`
branch from M1456 through M1465.

Decision:

```text
boundary_retarget_validation_synthesis_continue_with_dedup_repair
```

Synthesis decision:

```text
continue
```

M1466 does not run replay, train, run PPO, promote, use private holdout, export
corpus, or change actor inputs.

## Evidence Summary

This branch achieved three useful things:

```text
M1456-M1457:
  implemented and ran source-step boundary retarget proposal generation.
  Result: 798 proposals, 128 selected retarget candidates.

M1459-M1461:
  retargeted preflight passed and bounded replay produced actual positives.
  Result: 156 actual replay rows, 2 history positives, 8 zero-current controls.

M1463-M1465:
  designed and implemented positive-neighborhood expansion.
  Result: 24960 proposals, 192 selected candidates, but only 20 unique keys.
```

Compared with M1452, the branch improved the situation:

```text
M1452 history_positive_rows: 0
M1461 history_positive_rows: 2
```

So the core retargeting idea is alive.

## Supported Claims

Supported:

```text
source-step retargeting can move replay pressure toward an outcome-sensitive
boundary.

the current branch can produce real bounded-replay history-positive rows.

the positive-neighborhood generator can construct a broad proposal pool from
the live M1461 positive neighborhood.
```

## Falsified Or Unsupported Claims

Unsupported:

```text
M1461 positives are source-diverse enough for training.

M1465 selected_candidate_rows can be trusted without unique-key deduplication.

this branch has a corpus ready for PPO, distillation, promotion, or paper-level
self-identification claims.
```

## Failure Taxonomy Summary

Main failure types:

```text
scenario_sampling_failure:
  M1461 positives are real but source-singleton.

metric_artifact:
  M1465 selected_candidate_rows are inflated by duplicate positive_neighborhood_key rows.
```

The duplicate-key issue must be repaired before any preflight or replay rerun.

## Public Gate Overfit Risk

Risk:

```text
high
```

Reason:

```text
The branch now has a known live public positive source. Replaying or training
directly from duplicated versions of that source would likely create a
gate-passing artifact.
```

## Next Branch Decision

Continue the same branch, but reset the narrow-milestone counter after this
synthesis and require a dedup repair before more replay:

```text
M1467: deduplicate positive_neighborhood_key before selection
M1468: rerun proposal smoke
then:
  if unique selected surface is source-diverse, design preflight;
  if still singleton, synthesize or pivot back to source mining.
```

## Guardrails

M1466 guardrail status:

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
m1467-paper-route-positive-neighborhood-dedup-repair
```
