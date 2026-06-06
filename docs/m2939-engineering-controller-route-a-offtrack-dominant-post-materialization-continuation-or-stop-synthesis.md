# M2939 Engineering Controller Route A Offtrack-Dominant Post-Materialization Continuation Or Stop Synthesis

## Summary

- status: completed
- synthesis decision: `continue`
- decision: `continue_to_m2940_tradeoff_aware_candidate_design`
- manifest: `experiments/manifests/m2939-engineering-controller-route-a-offtrack-dominant-post-materialization-continuation-or-stop-synthesis.json`
- parent audit: `docs/m2938-engineering-controller-route-a-offtrack-dominant-tradeoff-aware-repair-redesign-materialization-result-audit.md`
- parent summary: `runs/m2937_engineering_controller_route_a_offtrack_dominant_tradeoff_aware_repair_redesign_materialization_preflight/summary.json`
- follow-up manifest: `experiments/manifests/m2940-engineering-controller-route-a-offtrack-dominant-tradeoff-aware-candidate-design.json`
- next: `m2940-engineering-controller-route-a-offtrack-dominant-tradeoff-aware-candidate-design`

M2939 synthesizes the M2934-M2938 Route A offtrack-dominant repair branch after the tradeoff-aware materialization audit. The branch should continue, but only through one bounded candidate-design milestone. It should not execute another fixed candidate, train, validate, rank, promote, or claim repair success.

## Evidence Summary

M2934 localized the fixed M2655 repair candidate's same-panel outcome shifts:

```text
panel rows: 56
offtrack target rows: 38
context rows: 18

offtrack -> success: 4
offtrack -> offtrack: 24
offtrack -> collision: 4
offtrack -> speed_too_low: 6
success -> offtrack: 5
success -> collision: 4
success -> success: 2
collision -> collision: 1
collision -> offtrack: 1
collision -> speed_too_low: 1
speed_too_low -> speed_too_low: 3
speed_too_low -> offtrack: 1
```

M2936 converted that result into a tradeoff-aware redesign requirement:

```text
persistent offtrack must be addressed directly
collision/speed substitution must be blocked
success-context rows must be retained
positive offtrack->success rows must remain references, not rankings
actor observation/action contract remains 72/3
```

M2937 materialized the design as machine-checkable rows:

```text
transition constraints: 56
persistent offtrack constraints: 24
collision/speed substitution constraints: 10
context-retention constraints: 9
positive reference rows: 4
candidate-surface rows: 5
actor guards: 12
claim boundary rows: 27
gate rows: 17
```

M2938 accepted M2937 as complete and claim-safe while preserving the negative and mixed character of the evidence.

## Supported Claims

- M2937 is a complete no-execution materialization of the M2936 tradeoff-aware redesign.
- The materialized surface preserves all 56 transition rows and all expected constraint counts.
- The active Route A repair question is now clearer than the earlier fixed-candidate question: any next candidate must handle persistent offtrack, collision/speed substitution, and context retention together.
- A bounded candidate-design milestone is justified because it changes the repair question and remains no-execution.

## Falsified Claims

- M2937/M2938 do not show repair success.
- M2937/M2938 do not show driver performance improvement.
- M2937/M2938 do not show validation readiness or validation result.
- M2937/M2938 do not identify a winner among checkpoints, source milestones, task families, environments, windows, severity bands, time bands, or candidate rows.
- M2937/M2938 do not support paper, current-sim, high-fidelity, full-driver, finite-window-vs-GRU, or self-ID claims.
- The fixed M2655 candidate should not be repeated as-is on the same surface.

## Failure Taxonomy Summary

The active failure is not a missing artifact. It is a mixed behavior tradeoff:

```text
persistent offtrack: 24/38 offtrack target rows
substitution failure: 10/38 offtrack targets shift to collision or speed_too_low
context regression: 9 previously successful context rows shift to offtrack or collision
positive reference: 4 offtrack target rows shift to success
```

This remains a behavior_regression and objective_overfit risk. A target-only offtrack repair could make the public offtrack count look better while increasing collision, low-speed, or context failures.

## Public Gate Overfit Risk

Risk remains medium. M2937 reduced overfit risk by forcing all negative tradeoffs into actor-invisible constraints, but the evidence still comes from a public diagnostic panel and one fixed candidate's outcome shifts.

M2940 must therefore stay design-only. It may define one candidate route, objective surface, and later materialization requirements, but it must not execute, rank, promote, or report validation/performance.

## Next Branch Decision

M2939 continues the branch to:

```text
m2940-engineering-controller-route-a-offtrack-dominant-tradeoff-aware-candidate-design
```

M2940 must design exactly one bounded tradeoff-aware candidate route. It must include:

```text
full 56-row accounting
24 persistent-offtrack constraints
10 collision/speed-substitution constraints
9 context-retention constraints
4 positive-reference rows
actor-invisible evaluator constraints
no hidden/oracle/future-target actor input
no execution, training, validation, ranking, promotion, repair-success, performance, paper, high-fidelity, full-driver, finite-window-vs-GRU, or self-ID claim
```

If M2940 cannot define a candidate design that handles all four constraint families together, the branch should stop or pivot instead of returning to another fixed-candidate execution.
