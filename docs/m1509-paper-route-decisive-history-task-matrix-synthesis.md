# M1509 Paper-Route Decisive History Task Matrix Synthesis

## Summary

M1509 synthesizes the M1499-M1508 decisive-history task-matrix branch before
continuing to fixed-policy runner work.

Synthesis decision:

```text
promote_to_next_branch
```

Decision:

```text
decisive_history_task_matrix_synthesis_promote_to_bounded_runner_branch
```

This milestone does not run rollout generation, replay, PPO, training,
promotion, private holdout, corpus export, actor-input changes, or level3
self-ID claims.

## Evidence Summary

M1498 stopped the standard profile scaling route because the public three-seed
profile pilot did not support finite-window history necessity or online-GRU
hidden advantage. M1499 therefore pivoted to decisive T4/T5 tasks.

M1499-M1508 then built the infrastructure in layers:

```text
M1499:
  designed T4 same-current/same-recent/different-older-history and T5
  terminal-boundary task families.

M1500:
  implemented metadata-only DecisiveHistoryTaskCandidate harness.

M1501:
  designed source families, seed namespaces, matching tolerances, diversity
  gates, and intervention requirements.

M1502:
  implemented source-plan planner and deterministic M1500-compatible rows.

M1503:
  public metadata planner smoke generated 66 rows, accepted 66, with 33 T4 and
  33 T5 metadata rows.

M1504:
  designed current-sim env-hook/spec mapping for all six source families.

M1505:
  implemented dry env-hook specs and artifacts; 12 specs across six source
  families, zero guardrail violations.

M1506:
  reset-only runtime smoke passed 6/6 source families after hook sampling
  repair; no env.step, policy replay, candidate materialization, or training.

M1507:
  designed measured rollout candidate generation with source traces, matching
  distances, terminal margins, and interventions.

M1508:
  implemented candidate materialization scaffolding and guards; synthetic smoke
  materialized two measured synthetic candidates and rejected one reset-only row.
```

## Supported Claims

The branch now supports these claims:

```text
1. T4/T5 task definitions and metadata harness exist.
2. Public source-plan metadata can satisfy scale/diversity smoke gates.
3. Current-sim env-hook specs can be generated for all six source families.
4. A tiny source-diverse reset-only runtime smoke can instantiate all six
   source-family env configs.
5. The materialization guard blocks reset-only rows from becoming candidates.
6. The project has a clear artifact contract for measured rollout candidate
   generation.
```

These are infrastructure and process claims. They are useful because they
remove ambiguity before costly rollout probes.

## Falsified Or Unsupported Claims

The branch does not yet support:

```text
real current-sim T4/T5 candidate existence;
same-current/same-recent older-history necessity;
wrong-history or delayed-history terminal degradation;
online-GRU level3 self-identification;
policy superiority;
training corpus export;
checkpoint promotion;
paper-level self-ID evidence.
```

M1506 also exposed a source-label risk:

```text
After reset repair, most one-seed source-family resets sampled aeb_feasible
labels, except t5_high_speed_close_obstacle which sampled drift_required.
```

That is acceptable for reset plumbing, but a rollout candidate probe must
actively measure and filter near-boundary / nontrivial terminal outcomes.

## Failure Taxonomy Summary

Observed or relevant failure classes:

```text
scenario_sampling_failure:
  Initial M1506 manual reset probe failed five of six source families because
  hook obstacle filters were too narrow for reset viability. Repaired by
  broadening reset-smoke label acceptance and removing max-threshold filters.

metric_artifact:
  Main risk for the next stage. Reset-only and synthetic smoke can look like
  progress but are not real rollout evidence.

contract_violation:
  Not observed in M1499-M1508; guardrails stayed false.

private_holdout_contamination:
  Not observed; private holdout not used.
```

## Public-Gate Overfit Risk

Risk level:

```text
medium
```

Reasons:

```text
The branch has many public infrastructure milestones and no private holdout.
Most evidence is metadata, reset-only, or synthetic.
The next probe will still be public and should be treated as development
evidence, not paper-level generalization.
```

Mitigations:

```text
keep runner budgets small and pre-registered;
write rejected rows with failure reasons;
do not tune from a private holdout;
do not export a training corpus from the first public probe;
require measured rollout/intervention margins before candidate materialization.
```

## Next Branch Decision

Decision:

```text
promote_to_next_branch
```

Rationale:

```text
The task-matrix infrastructure branch has done its job. Continuing under the
same branch name would mix infrastructure scaffolding with the next evidence
axis: bounded fixed-policy source trace collection.
```

New branch:

```text
paper_route_decisive_history_bounded_runner
```

Next milestone:

```text
m1510-paper-route-decisive-history-bounded-runner-design
```

M1510 should design the runner budget, public checkpoint, source-family caps,
snapshot steps, trace schema, and guardrails before implementing real source
rollout collection.

## Guardrails

```text
training_started: false
evaluation_started: false
replay_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
training_corpus_exported: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```
