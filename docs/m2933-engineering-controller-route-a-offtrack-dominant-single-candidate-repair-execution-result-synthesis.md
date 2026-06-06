# M2933 Engineering Controller Route A Offtrack-Dominant Single-Candidate Repair Execution Result Synthesis

## Summary

- status: completed
- synthesis decision: `continue`
- decision: `continue_to_m2934_outcome_shift_localization_preflight`
- parent audit: `docs/m2932-engineering-controller-route-a-offtrack-dominant-single-candidate-repair-execution-result-audit.md`
- parent summary: `runs/m2931_engineering_controller_route_a_offtrack_dominant_single_candidate_repair_execution_preflight/summary.json`
- follow-up manifest: `experiments/manifests/m2934-engineering-controller-route-a-offtrack-dominant-repair-execution-outcome-shift-localization-preflight.json`
- next: `m2934-engineering-controller-route-a-offtrack-dominant-repair-execution-outcome-shift-localization-preflight`

M2933 synthesizes the M2925-M2932 offtrack-dominant repair diagnostic chain. It accepts the artifact result from M2931/M2932, rejects direct repair-success interpretation, and selects one bounded evidence-reanalysis continuation: materialize row-level outcome shifts between the original M2919 diagnostic panel and the fixed-candidate M2931 repair diagnostic panel.

## Evidence Summary

M2919 established the 56-row dependency-facing diagnostic panel:

```text
M2919 rows: 56
M2919 failures: 0
M2919 outcomes: success 11, collision 3, off_track 38, speed_too_low 4
M2919 guardrails: M2877, Route B, and Route C not executed
M2919 claim boundary: no validation, ranking, repair-success, performance, paper, high-fidelity, full-driver, finite-window-vs-GRU, or self-ID claim
```

M2925-M2928 converted that panel into an offtrack-dominant repair-admission surface:

```text
offtrack repair-target rows: 38
non-offtrack context/regression rows: 18
coverage constraints: 27
shortcut exclusion families: 7
actor contract: observation 72, action 3
```

M2931 executed the fixed M2655 repair candidate over the full 56-row panel:

```text
M2931 rows: 56
M2931 failures: 0
M2931 outcomes: success 6, collision 9, off_track 32, speed_too_low 10
all selected metrics finite: true
coverage constraints preserved: true
actor and claim guards passed: true
```

The aggregate shift is mixed:

```text
off_track: 38 -> 32
success: 11 -> 6
collision: 3 -> 9
speed_too_low: 4 -> 10
```

The row-level transition audit shows why direct continuation would be unsafe:

```text
offtrack target rows:
  offtrack -> offtrack: 24
  offtrack -> success: 4
  offtrack -> collision: 4
  offtrack -> speed_too_low: 6

context/regression rows:
  success -> success: 2
  success -> offtrack: 5
  success -> collision: 4
  collision -> collision: 1
  collision -> offtrack: 1
  collision -> speed_too_low: 1
  speed_too_low -> speed_too_low: 3
  speed_too_low -> offtrack: 1
```

This is not a clean repair signal. M2931 found four offtrack-to-success repairs, but it also produced ten offtrack target regressions into collision or speed-too-low and nine context regressions from success into offtrack or collision.

## Supported Claims

- The fixed M2655 repair candidate can be executed over the full M2925 offtrack-dominant panel without infrastructure failures.
- The M2928 coverage constraints, shortcut exclusions, M2877 guardrails, Route B context, Route C context, and actor 72/action 3 contract remained intact.
- The M2931 result is a useful diagnostic transition surface candidate because it creates both positive and negative row-level shifts that can be localized.
- The next evidence-changing step should be outcome-shift localization, not another repair execution or training run.

## Falsified Claims

- M2931 does not show repair success.
- M2931 does not show driver performance improvement.
- M2931 does not show validation readiness or validation result.
- M2931 does not identify a winner among checkpoints, source milestones, task families, environments, windows, severity bands, time bands, or candidate rows.
- M2931 does not support paper, current-sim, high-fidelity, full-driver, finite-window-vs-GRU, or self-ID claims.
- The fixed M2655 repair candidate is not safe to promote or use as a new baseline from this evidence.

## Failure Taxonomy Summary

The active failure is a mixed outcome-shift pattern rather than a simple offtrack repair. Offtrack count improved in aggregate, but the diagnostic panel got less driver-like in other ways:

```text
offtrack targets still offtrack: 24/38
offtrack targets repaired to success: 4/38
offtrack targets shifted to collision or speed_too_low: 10/38
non-offtrack context rows preserved as success: 2/18
non-offtrack context rows regressed from success to offtrack/collision: 9/18
```

This is best classified as behavior_regression plus objective_overfit risk. The candidate may be reducing lateral/offtrack failure on some rows while trading it for collision or conservative speed failure elsewhere. That tradeoff must be localized before any new repair design.

## Public Gate Overfit Risk

Risk is medium-high if the branch continues directly into another fixed-candidate repair execution. M2931 used an already-materialized M2655 candidate and preserved boundaries, so it did not overfit by tuning inside M2931. But the result is still tied to a public diagnostic panel and a single candidate. Continuing without row-level transition localization would invite public-surface overinterpretation.

The next step reduces this risk by keeping all 56 rows, preserving context regressions, and making positive and negative shifts visible before any new design, training, validation, ranking, or promotion.

## Next Branch Decision

M2933 continues the branch exactly once into:

```text
m2934-engineering-controller-route-a-offtrack-dominant-repair-execution-outcome-shift-localization-preflight
```

M2934 must materialize, without new rollout or training:

```text
row-level M2919 -> M2931 outcome shifts
offtrack-target repair and regression rows
non-offtrack context regression rows
source/task/environment/window/severity/time transition aggregates
coverage, shortcut, actor, guardrail, claim, and gate rows
```

M2934 must reject repair-success, ranking, validation, performance, paper, high-fidelity, full-driver, finite-window-vs-GRU, and self-ID claims. If M2934 cannot identify a concrete failure-localization mechanism that supports a bounded next design, the branch should pivot or stop instead of running another fixed-candidate execution.
