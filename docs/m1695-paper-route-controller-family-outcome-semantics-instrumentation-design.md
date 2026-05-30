# M1695 Paper-Route Controller-Family Outcome-Semantics Instrumentation Design

- status: completed
- decision: `outcome_semantics_instrumentation_design_admit_logging_implementation`
- parent audit: `docs/m1694-paper-route-controller-family-full-rollout-result-audit.md`
- blocker: M1693 has `794/864` terminated non-collision non-completion rows
  without termination reason

## Summary

M1695 designs a logging-only instrumentation route so the M1693-style full
public rollout can be interpreted without changing actor inputs or policy
behavior.

This milestone is design-only. It does not run rollout, train, replay, run PPO,
promote, use private holdout, tune profiles, change actor observations, or claim
controller-family ranking, paper-level evidence, or level3 self-identification.

## Missing Evidence

M1693 rows currently include:

```text
terminated
truncated
collision
obstacle_completed
min_clearance_margin
steps
```

They do not include:

```text
termination_reason
outcome_bucket
obstacle_passed_raw
completion_reason
```

Because `_terminated(frame)` is a boolean, M1693 cannot distinguish:

```text
non_finite_state
off_track
obstacle_collision
speed_too_low
speed_too_high
yaw_rate_limit
max_steps_noncompletion
obstacle_pass
```

That distinction is necessary before interpreting raw success or comparing
controller families.

## Logging Contract

Instrumentation must be info/logging only.

Allowed:

```text
add info["termination_reason"]
add info["obstacle_passed_raw"]
add info["completion_reason"]
add episode row fields derived from info
add aggregate rows grouped by outcome_bucket / termination_reason
```

Forbidden:

```text
change actor observation
change reward
change dynamics
change termination behavior
change controller profile config
use termination reason as actor input
use profile-specific tuning
```

The actor input contract remains P0 human-view no-wheel no-oracle.

## Env-Side Design

Replace the internal boolean-only termination check with a reason-producing
helper:

```text
_termination_reason(frame) -> str | None
```

Reason priority should match current termination order:

```text
non_finite_state
off_track
obstacle_collision
speed_too_low
speed_too_high
yaw_rate_limit
None
```

Then keep the existing behavior:

```text
terminated = termination_reason is not None
```

The step semantics stay unchanged. `obstacle_completed` remains gated by
`not terminated`, but `obstacle_passed_raw` should record whether the obstacle
finish condition was geometrically satisfied before the termination gate.

## Episode Outcome Buckets

The M1696 implementation should derive a stable `outcome_bucket` in evaluation
rows:

```text
success_obstacle_pass
collision_failure
off_track_noncollision_noncompletion
speed_too_low_noncollision_noncompletion
speed_too_high_noncollision_noncompletion
yaw_rate_limit_noncollision_noncompletion
non_finite_state_noncollision_noncompletion
max_steps_noncompletion
other_terminated_noncompletion
```

Bucket precedence:

```text
if success:
  success_obstacle_pass
elif collision:
  collision_failure
elif terminated and termination_reason:
  f"{termination_reason}_noncollision_noncompletion"
elif truncated:
  max_steps_noncompletion
else:
  other_terminated_noncompletion
```

## Runner/Aggregate Design

The full-rollout runner should write:

```text
termination_reason
obstacle_passed_raw
completion_reason
outcome_bucket
```

It should also write:

```text
outcome_aggregate.csv
termination_reason_aggregate.csv
profile_outcome_aggregate.csv
```

These aggregates are still diagnostic only until audited.

## Rerun Policy

M1693 rows cannot be relabeled reliably because they lack the state values that
triggered termination. M1696 should implement instrumentation and tests without
rerunning the full rollout. A later M1697-style milestone should rerun the same
864-cell public workload with instrumentation enabled.

The rerun must preserve:

```text
same workload
same profile checkpoints
same deterministic seeds
same actor input contract
same no-training/no-replay/no-PPO/no-promotion guardrails
```

## Pass Criteria For Implementation

M1696 should pass if:

```text
termination_reason appears in env info;
obstacle_passed_raw appears in env info;
evaluate/run_episode rows include termination_reason and outcome_bucket;
M1693 runner schema can write outcome aggregates;
tests verify every termination reason path;
tests verify observation shape is unchanged;
no actor input fields are added;
no rollout/training/replay/PPO/promotion occurs in implementation.
```

## Decision

Admit M1696 logging-only outcome-semantics instrumentation implementation. Do
not interpret M1693 controller-family aggregates until an instrumented rerun is
available and audited.
