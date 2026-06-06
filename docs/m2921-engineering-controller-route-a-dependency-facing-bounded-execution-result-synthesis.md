# M2921 Engineering Controller Route A Dependency-Facing Bounded Execution Result Synthesis

## Metadata

- status: completed
- synthesis decision: `continue`
- decision: `continue_to_m2922_dependency_facing_failure_localization_materialization_preflight`
- manifest: `experiments/manifests/m2921-engineering-controller-route-a-dependency-facing-bounded-execution-result-synthesis.json`
- synthesis artifact: `docs/m2921-engineering-controller-route-a-dependency-facing-bounded-execution-result-synthesis.md`
- parent audit: `docs/m2920-engineering-controller-route-a-dependency-facing-evidence-surface-bounded-execution-result-audit.md`
- parent summary: `runs/m2919_engineering_controller_route_a_dependency_facing_evidence_surface_bounded_execution_preflight/summary.json`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2922-engineering-controller-route-a-dependency-facing-failure-localization-materialization-preflight.json`
- next: `m2922-engineering-controller-route-a-dependency-facing-failure-localization-materialization-preflight`

## Evidence Summary

M2911-M2920 moved the Route A engineering-controller branch from route
synthesis to a concrete dependency-facing closed-loop diagnostic surface:

```text
M2911: pivoted from Route B source-family insufficiency to Route A dependency-facing synthesis.
M2912-M2914: designed, materialized, and audited the dependency-facing evidence surface.
M2915-M2917: designed, materialized, and audited row-level execution admission.
M2918: admitted one bounded execution preflight over all 56 accepted rows.
M2919: executed all 56 admitted rows and registered M2920 audit.
M2920: accepted M2919 as complete and claim-safe but rejected direct interpretation.
```

The M2919 execution artifact is complete:

```text
candidate rows: 56
resolved rows: 56
bounded execution rows: 56
failure rows: 0
gate_matrix_pass: true
all selected metrics finite: true
actor contract: 72 observation / 3 action
hidden/oracle/future-target actor input: false
M2877 guard execution: false
Route B context execution: false
Route C context execution: false
```

The diagnostic behavior remains weak:

```text
success: 11
collision: 3
off_track: 38
speed_too_low: 4
```

Source-milestone split:

```text
M2737: 18 rows, 3 success, 2 collision, 12 off_track, 1 speed_too_low
M2746: 14 rows, 1 success, 0 collision, 10 off_track, 3 speed_too_low
M2807: 12 rows, 4 success, 0 collision, 8 off_track, 0 speed_too_low
M2816: 12 rows, 3 success, 1 collision, 8 off_track, 0 speed_too_low
```

Task-family split:

```text
T4: 31 rows, 5 success, 1 collision, 21 off_track, 4 speed_too_low
T5: 25 rows, 6 success, 2 collision, 17 off_track, 0 speed_too_low
```

## Supported Claims

M2921 supports these bounded claims:

```text
M2919 produced complete Route A dependency-facing diagnostic execution artifacts.
M2919 preserved the actor input and action contract.
M2919 preserved M2877, Route B, and Route C guardrail boundaries.
M2919 diagnostic rows are sufficient input for failure localization.
The next useful Route A step should explain failure structure before another execution.
```

These claims are engineering-process and diagnostic claims only. They are not
driver-performance, validation, paper, high-fidelity, finite-window-vs-GRU,
current-sim verdict, full-driver, or self-ID claims.

## Falsified Claims

M2919 falsifies direct positive interpretation of this branch:

```text
The dependency-facing admitted surface is not a clean success surface.
M2919 does not show validation readiness.
M2919 does not support a controller-family, source-family, task-family, or profile ranking.
M2919 does not support repair success or checkpoint promotion.
M2919 does not support current-sim, paper, high-fidelity, full-driver, finite-window-vs-GRU, or self-ID verdicts.
```

This does not falsify the long-term Route A engineering-controller project. It
does falsify the shortcut of treating M2919 row accounting as a performance
result.

## Failure Taxonomy Summary

The dominant failure mode is off-track termination:

```text
off_track rows: 38 / 56
collision rows: 3 / 56
speed_too_low rows: 4 / 56
diagnostic success rows: 11 / 56
```

The source split suggests the weakness is broad rather than isolated to one
source milestone:

```text
M2737 off_track or collision or speed_too_low: 15 / 18
M2746 off_track or collision or speed_too_low: 13 / 14
M2807 off_track or collision or speed_too_low: 8 / 12
M2816 off_track or collision or speed_too_low: 9 / 12
```

The task-family split is also broad:

```text
T4 non-success rows: 26 / 31
T5 non-success rows: 19 / 25
```

The next evidence-changing step is not another broad 56-row execution. It is a
row-level localization materialization that asks which failure slices are
actionable:

```text
outcome bucket and termination localization
source-milestone by task-family localization
checkpoint-family localization
T4/T5 and source-edge localization
guardrail-preserving candidate next routes
```

## Public Gate Overfit Risk

Public-gate overfit risk is medium if the branch repeats M2919-like execution
without changing the surface. The run already executed all 56 admitted rows, so
rerunning the same surface mostly measures seed noise and does not change the
claim boundary.

The lower-risk continuation is a no-execution failure-localization
materialization. It uses the complete M2919 surface, keeps every weak row
visible, and prevents cherry-picking only the 11 success rows.

M2921 therefore rejects:

```text
another immediate M2919-like broad execution
direct tuning against only success rows
direct promotion or ranking from the 56 rows
direct Route B paper claim from Route A diagnostics
direct Route C high-fidelity claim without source availability
```

## Next Branch Decision

M2921 chooses `continue`, but only through a no-execution evidence reanalysis:

```text
m2922-engineering-controller-route-a-dependency-facing-failure-localization-materialization-preflight
```

M2922 must materialize a machine-checkable failure-localization panel from
M2919 artifacts before any repair, training, validation, ranking, promotion, or
new execution. It should write outcome-family rows, source-milestone/task-family
aggregates, checkpoint-family aggregates, next-route candidate rows, guardrail
context rows, actor-contract rows, claim-boundary rows, gate rows, a summary,
and an audit manifest.

Allowed M2922 claim:

```text
M2922 materializes M2919 failure localization and next-route candidates for a later audit.
```

Rejected M2922 claims:

```text
repair success
driver performance
validation readiness or result
ranking or winner selection
checkpoint promotion
paper evidence
finite-window-vs-GRU conclusion
current-sim verdict
high-fidelity validation readiness or result
full ideal driver completion
level3 self-identification
```
