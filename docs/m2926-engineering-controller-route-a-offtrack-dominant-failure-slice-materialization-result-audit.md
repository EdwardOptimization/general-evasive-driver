# M2926 Engineering Controller Route A Offtrack-Dominant Failure Slice Materialization Result Audit

## Summary

- status: completed
- decision: `accept_m2925_offtrack_slice_claim_safe_route_to_m2927_branch_synthesis`
- audited artifact: `runs/m2925_engineering_controller_route_a_offtrack_dominant_failure_slice_materialization_preflight/summary.json`
- follow-up manifest: `experiments/manifests/m2927-engineering-controller-route-a-offtrack-dominant-localization-branch-synthesis.json`
- next: `m2927-engineering-controller-route-a-offtrack-dominant-localization-branch-synthesis`

M2926 accepts M2925 as a complete and claim-safe no-execution materialization. M2925 accounts for all 56 M2919 diagnostic rows, materializes exactly 38 off_track rows, preserves exactly 18 non-offtrack context rows, writes all required slice/context/guard/actor/claim/gate artifacts, and keeps actor and claim boundaries intact.

## Audited Facts

- M2925 `status_pass`: true
- M2925 `gate_matrix_pass`: true
- execution rows read: 56
- offtrack rows materialized: 38
- non-offtrack context rows preserved: 18
- source split: M2737 12, M2746 10, M2807 8, M2816 8
- task split: T4 21, T5 17
- checkpoint context split: public pilot L3 checkpoint 28, M2655 mitigation-preserving checkpoint 10
- environment split: t5_near_boundary_warmup 12, t4_capability_step_temporal 9, t4_actuator_delay_response 8, t5_boundary_axis_retarget 5, t4_staged_warmup_capability 4
- window split: mapping_window_unspecified 20, reveal_plus_4 9, decision_minus_32 5, decision_minus_24 4
- overshoot band split: low 5, medium 20, high 13
- time-to-offtrack split: early 9, mid 20, late 9
- actor contract: observation 72, action 3
- actor guard rows pass: true
- gate rows: 21

M2925 does not run reset, step, rollout, replay, validation, training, PPO, dependency work, ranking, winner selection, or promotion. It does not expose hidden/oracle/future-target labels or route/source/diagnostic/verdict labels to actor input.

## Boundary Audit

The M2925 rows are accepted only as localization artifacts. Counts across source, task, checkpoint, environment, window, overshoot, and time bands are not rankings and do not identify a winner. The larger public-pilot checkpoint count and t5_near_boundary_warmup count are useful for repair admission planning only because they help preserve coverage and denominator accounting.

M2877 fixed weak diagnostic rows, Route B source-family insufficiency, and Route C source_unavailable remain guardrail/context rows. They are not executed and are not admitted into validation, paper, high-fidelity readiness, or self-ID denominators.

Rejected interpretations:

```text
repair success, driver performance, validation readiness, validation result, source/task/checkpoint/environment/window/severity/time-band ranking, winner selection, checkpoint promotion, success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity validation readiness or result, full ideal driver completion, or level3 self-identification
```

## Decision

M2926 selects exactly one next route:

```text
m2927-engineering-controller-route-a-offtrack-dominant-localization-branch-synthesis
```

The selected route is a branch synthesis gate. The local-search guard has fired after consecutive no-execution localization/audit/design milestones, so the branch must synthesize M2919-M2926 evidence before another repair-admission design. M2927 must decide continue, pivot, stop, or promote_to_next_branch while preserving all 38 offtrack rows, all 18 non-offtrack context rows, and all M2877/Route B/Route C guardrails. It must not execute policy/environment work, train, validate, rank, promote, or claim performance.
