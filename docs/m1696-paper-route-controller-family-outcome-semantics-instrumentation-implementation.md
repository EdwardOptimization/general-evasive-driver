# M1696 Paper-Route Controller-Family Outcome-Semantics Instrumentation Implementation

- status: completed
- decision: `outcome_semantics_instrumentation_implementation_pass_route_to_instrumented_rerun_design`
- parent design: `docs/m1695-paper-route-controller-family-outcome-semantics-instrumentation-design.md`

## Summary

M1696 implements logging-only outcome-semantics instrumentation.

This milestone does not execute the full 864-cell rollout, train, replay, run
PPO, promote, use private holdout, tune profiles, change actor inputs, change
reward, change dynamics, or change termination behavior.

## Implemented Logging

Environment `info` now includes:

```text
termination_reason
obstacle_passed_raw
completion_reason
```

`termination_reason` is produced by `_termination_reason(frame)` with the same
priority as the existing boolean termination logic:

```text
non_finite_state
off_track
obstacle_collision
speed_too_low
speed_too_high
yaw_rate_limit
```

The existing `_terminated(frame)` remains behaviorally equivalent:

```text
_terminated(frame) == (_termination_reason(frame) is not None)
```

Evaluation rows now include:

```text
termination_reason
obstacle_passed_raw
completion_reason
outcome_bucket
```

The full-rollout runner can now write:

```text
outcome_aggregate.csv
termination_reason_aggregate.csv
profile_outcome_aggregate.csv
```

## Contract Boundary

The actor observation contract is unchanged.

- no actor observation fields added
- no reward changes
- no dynamics changes
- no termination behavior changes
- no policy behavior changes
- instrumentation is info/logging only

## Verification

Commands run:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_env.py tests/test_evaluate.py tests/test_controller_family_full_rollout_execution.py
```

Result:

```text
55 passed
```

Focused tests cover:

- env info includes new fields
- obstacle collision reports `termination_reason == obstacle_collision`
- obstacle pass reports `obstacle_passed_raw == true` and
  `completion_reason == obstacle_pass`
- termination penalty path reports `off_track`
- all termination reason paths can be queried directly
- observation shape remains unchanged
- evaluation rows include outcome semantics fields
- outcome bucket classification
- profile-outcome aggregate generation

## Supported Claims

- Outcome semantics can be logged without changing actor inputs or policy
  behavior.
- The next full public rollout can be instrumented to distinguish collision,
  obstacle pass, max-step noncompletion, and reason-specific noncollision
  terminations.

## Unsupported Claims

- controller-family ranking
- finite-window history necessity
- recurrent advantage
- paper-level evidence
- private-holdout evidence
- level3 self-identification

## Decision

M1696 passes as logging-only instrumentation. Route to M1697 instrumented rerun
design before executing the full workload again.
