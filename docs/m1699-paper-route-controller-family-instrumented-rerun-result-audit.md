# M1699 Paper-Route Controller-Family Instrumented Rerun Result Audit

- status: completed
- decision: `instrumented_rerun_audit_blocks_ranking_route_to_branch_synthesis`
- audited artifact: `runs/m1698_controller_family_instrumented_full_rollout/summary.json`
- audited outcome aggregate: `runs/m1698_controller_family_instrumented_full_rollout/outcome_aggregate.csv`
- audited termination aggregate: `runs/m1698_controller_family_instrumented_full_rollout/termination_reason_aggregate.csv`

## Audit Result

M1698 is a clean instrumented public execution pass.

- episode count: `864`
- profile count: `12`
- spec count: `72`
- failure count: `0`
- selected metrics finite: `true`
- guardrail violation count: `0`
- outcome aggregate rows: `3`
- termination reason aggregate rows: `3`
- profile outcome aggregate rows: `22`

## Outcome Interpretation

The instrumentation resolves the M1694 ambiguity. The dominant non-success mode
is off-track, not obstacle collision:

| outcome bucket | count | share |
| --- | ---: | ---: |
| success_obstacle_pass | 32 | 0.0370 |
| collision_failure | 38 | 0.0440 |
| off_track_noncollision_noncompletion | 794 | 0.9190 |

Termination reasons:

| termination reason | count |
| --- | ---: |
| none | 32 |
| obstacle_collision | 36 |
| off_track | 796 |

The two-count difference between collision failures and `obstacle_collision`
termination reason comes from priority: `off_track` is checked before
`obstacle_collision`, while `outcome_bucket` still preserves collision failures.

## Consequence

M1698 cannot support controller-family ranking or recurrent-advantage claims.
The current measured workload is dominated by road-boundary termination. Ranking
controllers by raw success would conflate:

```text
obstacle avoidance
road-boundary keeping
completion/finish semantics
task geometry strictness
```

This is useful evidence, but it is not the paper comparison yet.

## Required Next Route

The branch has also reached its synthesis cadence: M1690 through M1699 form ten
milestones after the previous synthesis.

The next milestone must be branch synthesis, not another narrow rollout or
profile tweak. That synthesis should decide whether to pivot to:

```text
outcome-semantics task-quality branch;
corridor/boundary calibration branch;
conditional obstacle-avoidance metric branch;
or a redesigned controller-family comparison workload.
```

## Supported Claims

- Instrumentation works and produces interpretable outcome buckets.
- The dominant blocker in the current workload is off-track non-collision
  non-completion.
- A raw controller-family ranking from M1693/M1698 would be misleading.
- Branch synthesis is required before more task-specific implementation.

## Unsupported Claims

- controller-family ranking
- finite-window history necessity
- recurrent advantage
- private-holdout generalization
- paper-level evidence
- level3 anticipatory self-identification

## Decision

M1699 passes as an instrumented-result audit. Route to M1700 branch synthesis and
keep training, replay, PPO, promotion, private holdout, actor-input changes, and
controller-family ranking blocked.
