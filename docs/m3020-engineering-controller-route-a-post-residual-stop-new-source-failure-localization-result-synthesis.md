# M3020 Engineering Controller Route A Post-Residual-Stop New Source Failure Localization Result Synthesis

## Metadata

- status: completed
- synthesis decision: `continue_to_m3021_new_source_broad_failure_objective_admission_design`
- manifest: `experiments/manifests/m3020-engineering-controller-route-a-post-residual-stop-new-source-failure-localization-result-synthesis.json`
- parent audit: `docs/m3019-engineering-controller-route-a-post-residual-stop-new-source-failure-localization-materialization-result-audit.md`
- parent preflight: `runs/m3018_engineering_controller_route_a_post_residual_stop_new_source_failure_localization_materialization_preflight/summary.json`
- follow-up manifest: `experiments/manifests/m3021-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-objective-admission-design.json`
- next: `m3021-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-objective-admission-design`

M3020 is synthesis-only. It does not reset, step, rollout, replay, validate,
train, rank, promote, mutate checkpoints, tune profiles, select a winner, or
claim performance.

## Evidence Summary

M3018/M3019 support a narrow claim:

```text
M3018 materialized complete, claim-safe failure-localization artifacts.
M3019 accepted M3018 as complete and claim-safe.
M3018 preserved 16 M3006 task_source ids and 32 M3015 diagnostic rows.
Failure localization rows: 32.
Profile/source aggregate rows: 32.
Actor contract: observation 72, action 3.
```

The localized diagnostic distribution is broad and negative:

```text
success rows: 3
collision rows: 5
off_track terminations: 23
obstacle_collision terminations: 4
speed_too_low terminations: 2
blank termination rows: 3
```

Profile-level localization:

```text
candidate profile: 0 success, 12 off_track, 2 collision, 2 speed_too_low
parent profile: 3 success, 10 off_track, 3 collision
both profiles non-success on 13 of 16 task_source ids
parent success with candidate failure on 3 of 16 task_source ids
```

These facts are useful for route design only. They are not a validation result,
repair-success result, driver-performance result, paper result, current-sim
verdict, high-fidelity readiness result, finite-window-vs-GRU result,
full-driver result, ranking result, promotion result, or self-ID result.

## Supported Claims

M3020 supports only these claims:

```text
M3018/M3019 artifacts are complete and claim-safe enough for a follow-up design route.
The M3015 new-source surface is broad negative diagnostic evidence, not a validation surface.
Direct repair target selection is not justified from M3018 localization alone.
An objective-admission design route is justified before any target materialization, fitting, execution, ranking, or promotion.
```

## Falsified Or Unsupported Claims

M3020 rejects these claims:

```text
driver performance improved
repair succeeded
M3015 validates the candidate checkpoint
M3018 ranks candidate versus parent
M3018 justifies winner selection or promotion
M3018 is paper evidence
M3018 changes the current-sim verdict
M3018 establishes high-fidelity readiness
M3018 decides finite-window-vs-GRU
M3018 advances full ideal driver completion
M3018 establishes level3 self-identification
```

## Failure Taxonomy Summary

The dominant non-success family is offtrack recovery failure. Collision and
speed-floor failures remain secondary but non-negligible. The failure is not
limited to one task_source id or one profile: most task_source ids fail under
both candidate and parent. The candidate is not suitable for ranking or
promotion because it has zero success rows on this diagnostic surface.

The next route should therefore be design-only and objective-admission focused:
it may decide how to express broad offtrack-dominant failures with collision
and speed-floor guards, but it must not materialize targets, train, execute,
rank, tune, or claim repair success.

## Public Gate Overfit Risk

Continuing directly to repair, target fitting, ranking, or promotion would risk
optimizing against the newly exposed 32-row diagnostic surface. The next step
must keep the route at admission/design level and preserve all claim boundaries.

## Next Branch Decision

M3020 continues exactly once to:

```text
m3021-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-objective-admission-design
```

M3021 must be design-only. It may inspect M3018/M3019/M3020 evidence and decide
whether a no-training objective-admission route is legal. It must not run
episodes, materialize numeric targets, fit/train, rank, promote, mutate
checkpoints, tune profiles, validate, or claim performance.

## Stop Conditions For The Next Route

M3021 must stop or route to synthesis if:

```text
it cannot define an objective-admission route without selecting a repair target prematurely
it needs another rollout, profile mutation, or checkpoint mutation
it would convert diagnostic counts into a performance verdict
it cannot preserve offtrack, collision, speed-floor, and success guard context
```
