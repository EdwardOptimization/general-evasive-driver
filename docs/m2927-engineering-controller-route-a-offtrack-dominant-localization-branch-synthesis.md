# M2927 Engineering Controller Route A Offtrack-Dominant Localization Branch Synthesis

## Summary

- status: completed
- synthesis decision: `continue`
- decision: `continue_to_m2928_offtrack_dominant_repair_admission_materialization_preflight`
- parent audit: `docs/m2926-engineering-controller-route-a-offtrack-dominant-failure-slice-materialization-result-audit.md`
- follow-up manifest: `experiments/manifests/m2928-engineering-controller-route-a-offtrack-dominant-repair-admission-materialization-preflight.json`
- next: `m2928-engineering-controller-route-a-offtrack-dominant-repair-admission-materialization-preflight`

M2927 synthesizes the M2919-M2926 offtrack-localization branch because the local-search guard fired after consecutive no-execution process milestones. The branch has produced useful localization evidence and clean accounting, but it has not improved driver behavior and cannot support performance, validation, paper, high-fidelity, full-driver, or self-ID claims.

## Evidence Summary

M2919 generated 56 claim-bounded Route A diagnostic rows with 11 success, 3 collision, 38 off_track, and 4 speed_too_low outcomes. M2920 accepted those rows as complete and claim-safe but not performance evidence. M2921 chose failure localization rather than broad rerun. M2922 materialized outcome/source/task/checkpoint candidate rows and preserved guardrails. M2923 accepted that materialization and selected the offtrack-dominant route. M2924 designed an offtrack slice contract. M2925 materialized 38 offtrack rows plus 18 non-offtrack context rows. M2926 accepted M2925 as complete and claim-safe.

The strongest localized fact is not a winner or score: off_track dominates the weak outcome family and is distributed across all four source milestones, both task families, both checkpoint contexts, five environment templates, four window tags, three overshoot bands, and three time-to-offtrack bands.

## Supported Claims

- The branch has a complete offtrack-localization artifact chain over the accepted M2919 rows.
- The actor contract remains observation 72 and action 3.
- M2877 fixed weak diagnostic rows, Route B source-family insufficiency, and Route C source_unavailable remain guardrail/context rows.
- The next evidence-changing Route A step should be repair-admission materialization, not another broad diagnostic rerun.

## Falsified Claims

- M2919-M2926 do not show repair success.
- M2919-M2926 do not show driver performance improvement.
- M2919-M2926 do not show validation readiness or validation result.
- M2919-M2926 do not support finite-window-vs-GRU, current-sim, high-fidelity, paper, full-driver, or self-ID claims.
- The offtrack slice counts do not rank checkpoints, source milestones, task families, environment templates, windows, or severity/time bands.

## Failure Taxonomy Summary

The active failure family remains offtrack-dominant weak diagnostic behavior. The branch converted a broad 56-row diagnostic result into a materialized slice panel:

- source split: M2737 12, M2746 10, M2807 8, M2816 8
- task split: T4 21, T5 17
- checkpoint context: public pilot L3 28, M2655 mitigation-preserving 10
- environment split: t5_near_boundary_warmup 12, t4_capability_step_temporal 9, t4_actuator_delay_response 8, t5_boundary_axis_retarget 5, t4_staged_warmup_capability 4
- overshoot bands: low 5, medium 20, high 13
- time-to-offtrack bands: early 9, mid 20, late 9

This is sufficient for repair-admission materialization, not for repair execution.

## Public Gate Overfit Risk

Risk is medium. The branch is still anchored to accepted M2919 diagnostics and existing checkpoints. It did not tune a controller, rerun until a public row passed, rank slices, or select a winner. The next route must preserve the 38 offtrack rows and 18 context rows as coverage constraints and must not collapse to a narrow public slice.

## Next Branch Decision

M2927 continues the branch exactly once into M2928 repair-admission materialization. M2928 should materialize repair-admission rows that define:

- admitted repair hypothesis families
- excluded shortcut families
- required coverage constraints over the 38 offtrack rows and 18 context rows
- actor contract and label-visibility guards
- allowed future execution preflight criteria
- blocked performance, validation, ranking, promotion, paper, high-fidelity, full-driver, and self-ID claims

M2928 must not execute reset, rollout, validation, training, PPO, dependency work, ranking, winner selection, or promotion. If M2928 cannot produce a concrete materialized admission surface, the branch should pivot or stop rather than continue process-only work.
