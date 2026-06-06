# M2923 Engineering Controller Route A Dependency-Facing Failure Localization Materialization Result Audit

## Summary

- status: completed
- decision: `accept_m2922_failure_localization_claim_safe_route_to_m2924_offtrack_dominant_failure_slice_design`
- audited artifact: `runs/m2922_engineering_controller_route_a_dependency_facing_failure_localization_materialization_preflight/summary.json`
- follow-up manifest: `experiments/manifests/m2924-engineering-controller-route-a-offtrack-dominant-failure-slice-design.json`
- next: `m2924-engineering-controller-route-a-offtrack-dominant-failure-slice-design`

M2923 accepts M2922 as a complete and claim-safe no-execution failure-localization materialization. M2922 accounts for all 56 M2919 diagnostic execution rows, preserves the 0 failure-row accounting state, writes the required outcome/source/task/checkpoint/next-route/guard/actor/claim/gate artifacts, and keeps actor input and claim boundaries intact.

## Audited Facts

- M2922 `status_pass`: true
- M2922 `gate_matrix_pass`: true
- localized execution rows: 56
- execution failure rows: 0
- outcome counts: 11 diagnostic success, 3 collision, 38 off_track, 4 speed_too_low
- source split: M2737 18, M2746 14, M2807 12, M2816 12
- task split: T4 31, T5 25
- checkpoint outcome rows: 2
- next-route candidate rows: 4
- admitted next-route candidates for audit: 4
- guardrail context rows: 46
- actor guard rows pass: true
- claim boundary rows: 29
- gate rows: 19

M2922 does not run reset, step, rollout, replay, validation, training, PPO, dependency work, ranking, winner selection, or promotion. The actor contract remains observation 72 and action 3, and the materialized rows do not expose hidden/oracle/future-target labels or route/source/diagnostic/verdict labels to actor input.

## Boundary Audit

The M2922 next-route rows are accepted only as audit candidates. They are not rankings, winners, or performance verdicts. The off_track candidate has the largest diagnostic count, but M2923 treats that fact as a failure-localization priority because it covers the dominant weak outcome family, not as a controller, checkpoint, task, or source-family quality comparison.

M2877 fixed weak diagnostic rows, Route B source-family insufficiency, and Route C source_unavailable remain guardrail/context rows. They are not executed and are not admitted into validation, paper, high-fidelity readiness, or self-ID denominators.

Rejected interpretations:

```text
repair success, driver performance, validation readiness, validation result, controller/source/task/checkpoint ranking, winner selection, checkpoint promotion, success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity validation readiness or result, full ideal driver completion, or level3 self-identification
```

## Decision

M2923 selects exactly one next route:

```text
m2924-engineering-controller-route-a-offtrack-dominant-failure-slice-design
```

The selected route is a design-only offtrack-dominant failure-slice plan. It should convert M2922's 38 off_track rows plus source/task/checkpoint context into a bounded investigation plan before any repair execution. It may define slices, required materialization rows, denominator rules, guardrails, and a follow-up materialization preflight. It must not execute policy/environment work, train, validate, rank, promote, or claim performance.

The source-milestone, task-family, and checkpoint-context candidates remain supporting context for M2924. They are not separately selected as parallel routes in M2923.
