# M2924 Engineering Controller Route A Offtrack-Dominant Failure Slice Design

## Summary

- status: completed
- decision: `admit_m2925_offtrack_dominant_failure_slice_materialization_preflight`
- parent audit: `docs/m2923-engineering-controller-route-a-dependency-facing-failure-localization-materialization-result-audit.md`
- parent materialization: `runs/m2922_engineering_controller_route_a_dependency_facing_failure_localization_materialization_preflight/summary.json`
- follow-up manifest: `experiments/manifests/m2925-engineering-controller-route-a-offtrack-dominant-failure-slice-materialization-preflight.json`
- next: `m2925-engineering-controller-route-a-offtrack-dominant-failure-slice-materialization-preflight`

M2924 designs a no-execution offtrack-dominant failure-slice materialization route. It accepts M2923's audit decision and uses M2922/M2919 diagnostic rows only as already-recorded evidence. It does not run reset, step, rollout, replay, validation, training, dependency work, ranking, winner selection, promotion, or performance evaluation.

## Input Facts

- M2922 localized 56 M2919 diagnostic execution rows.
- M2922/M2919 outcome split: 11 diagnostic success, 3 collision, 38 off_track, 4 speed_too_low.
- M2923 selects the off_track route because off_track is the dominant weak diagnostic outcome, not because it is a performance ranking or winner.
- M2877 fixed weak diagnostic rows, Route B source-family insufficiency, and Route C source_unavailable remain guardrail/context rows.
- Actor contract remains observation 72 and action 3 with no hidden/oracle/future-target actor input.

## Offtrack Slice Contract

M2925 must materialize the 38 off_track rows into explicit slice rows while preserving all 56 rows as the diagnostic denominator and preserving the 18 non-offtrack rows as context. The required no-execution slice dimensions are:

- outcome denominator: 38 off_track rows and 18 non-offtrack context rows.
- source milestone: M2737 12, M2746 10, M2807 8, M2816 8.
- task family: T4 21, T5 17.
- checkpoint context: public pilot L3 checkpoint 28, M2655 mitigation-preserving checkpoint 10.
- environment template: t5_near_boundary_warmup 12, t4_capability_step_temporal 9, t4_actuator_delay_response 8, t5_boundary_axis_retarget 5, t4_staged_warmup_capability 4.
- window tag: mapping_window_unspecified 20, reveal_plus_4 9, decision_minus_32 5, decision_minus_24 4.
- history length: profile_env_history_length 1 for all 38 off_track rows.
- overshoot band from `off_track_severity_proxy`: low <= 0.02 has 5 rows, medium <= 0.08 has 20 rows, high > 0.08 has 13 rows.
- time-to-offtrack band: early <= 1.75s has 9 rows, mid <= 2.5s has 20 rows, late > 2.5s has 9 rows.

These dimensions are allowed for localization and materialization only. M2925 must not rank source milestones, task families, checkpoints, environment templates, windows, or severity bands.

## Required M2925 Artifacts

M2925 must write:

- `summary.json`
- `offtrack_slice_rows.csv`
- `offtrack_source_slice_rows.csv`
- `offtrack_task_slice_rows.csv`
- `offtrack_checkpoint_slice_rows.csv`
- `offtrack_environment_slice_rows.csv`
- `offtrack_window_slice_rows.csv`
- `offtrack_severity_slice_rows.csv`
- `non_offtrack_context_rows.csv`
- `guardrail_context_rows.csv`
- `actor_contract_guard_rows.csv`
- `claim_boundary_rows.csv`
- `gate_matrix.csv`
- `run_state.json`
- `docs/m2925-engineering-controller-route-a-offtrack-dominant-failure-slice-materialization-preflight.md`
- one follow-up result-audit manifest

The gates must require full accounting of the 38 off_track rows, explicit preservation of the 18 non-offtrack context rows, preservation of M2877/Route B/Route C guardrails, actor 72/action 3, no hidden/oracle/future-target actor input, no actor-visible labels, no execution, no ranking, and no overclaim.

## Rejected Routes

- direct repair execution from M2922 or M2924
- another broad M2919-like rerun before offtrack slice materialization
- validation or performance interpretation of the 38 off_track rows
- source/task/checkpoint ranking
- checkpoint promotion or winner selection
- paper, finite-window-vs-GRU, current-sim, high-fidelity, full-driver, or self-ID claim

## Decision

M2924 admits M2925 as a materialization preflight. M2925 should convert this design into machine-checkable rows only; it must register M2926 result audit before any interpretation or repair design.
