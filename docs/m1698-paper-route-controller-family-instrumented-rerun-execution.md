# M1698 Paper-Route Controller-Family Instrumented Rerun Execution

- status: completed
- result class: `controller_family_full_rollout_execution_pass`
- output: `runs/m1698_controller_family_instrumented_full_rollout`
- parent design: `docs/m1697-paper-route-controller-family-instrumented-rerun-design.md`

## Summary

M1698 executed the same 864-cell public controller-family workload as M1693
with M1696 outcome-semantics instrumentation enabled.

This milestone ran public evaluation only. It did not train, replay, run PPO,
promote, use private holdout, tune profiles, change actor inputs, or claim
controller-family ranking, paper-level evidence, or level3 self-identification.

## Execution Result

- episode count: `864`
- profile count: `12`
- spec count: `72`
- failure count: `0`
- selected metrics finite: `true`
- guardrail violation count: `0`
- outcome aggregate rows: `3`
- termination reason aggregate rows: `3`
- profile outcome aggregate rows: `22`

Required artifacts were written:

```text
runs/m1698_controller_family_instrumented_full_rollout/summary.json
runs/m1698_controller_family_instrumented_full_rollout/episode_rows.csv
runs/m1698_controller_family_instrumented_full_rollout/profile_aggregate.csv
runs/m1698_controller_family_instrumented_full_rollout/spec_aggregate.csv
runs/m1698_controller_family_instrumented_full_rollout/stratum_aggregate.csv
runs/m1698_controller_family_instrumented_full_rollout/comparison_aggregate.csv
runs/m1698_controller_family_instrumented_full_rollout/outcome_aggregate.csv
runs/m1698_controller_family_instrumented_full_rollout/termination_reason_aggregate.csv
runs/m1698_controller_family_instrumented_full_rollout/profile_outcome_aggregate.csv
runs/m1698_controller_family_instrumented_full_rollout/failure_rows.csv
runs/m1698_controller_family_instrumented_full_rollout/run_state.json
```

## Outcome Snapshot

These are diagnostic execution outputs only and must be audited before any
controller-family comparison claim.

| outcome_bucket | count | success_rate | collision_rate | clearance_margin_mean |
| --- | ---: | ---: | ---: | ---: |
| success_obstacle_pass | 32 | 1.0000 | 0.0000 | 2.6313 |
| collision_failure | 38 | 0.0000 | 1.0000 | -0.0699 |
| off_track_noncollision_noncompletion | 794 | 0.0000 | 0.0000 | 11.4088 |

Termination reason rows:

| termination_reason | count |
| --- | ---: |
| none | 32 |
| obstacle_collision | 36 |
| off_track | 796 |

The small mismatch between collision failures and `obstacle_collision` reason is
expected from termination-reason priority: `off_track` is checked before
`obstacle_collision`, while `outcome_bucket` still preserves collision failures.

## Supported Claims

- The M1693 workload can rerun with outcome-semantics instrumentation.
- Outcome, termination-reason, and profile-outcome aggregates are now available
  for audit.
- The dominant non-success outcome is explicitly identified as off-track
  non-collision non-completion, not obstacle collision.

## Unsupported Claims

- controller-family ranking
- finite-window history necessity
- recurrent advantage
- private-holdout generalization
- paper-level evidence
- level3 anticipatory self-identification

## Decision

M1698 passes as instrumented public rerun execution. Route to M1699 result audit
before interpreting controller-family diagnostics or modifying the workload.
