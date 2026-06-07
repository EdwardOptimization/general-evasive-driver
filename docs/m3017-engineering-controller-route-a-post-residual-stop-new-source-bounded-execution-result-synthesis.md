# M3017 Engineering Controller Route A Post-Residual-Stop New Source Bounded Execution Result Synthesis

## Metadata

- status: completed
- synthesis decision: `continue_to_m3018_new_source_failure_localization_materialization_preflight`
- manifest: `experiments/manifests/m3017-engineering-controller-route-a-post-residual-stop-new-source-bounded-execution-result-synthesis.json`
- parent audit: `docs/m3016-engineering-controller-route-a-post-residual-stop-new-source-bounded-execution-result-audit.md`
- parent preflight: `runs/m3015_engineering_controller_route_a_post_residual_stop_new_source_bounded_execution_preflight/summary.json`
- follow-up manifest: `experiments/manifests/m3018-engineering-controller-route-a-post-residual-stop-new-source-failure-localization-materialization-preflight.json`
- next: `m3018-engineering-controller-route-a-post-residual-stop-new-source-failure-localization-materialization-preflight`

M3017 is synthesis-only. It does not reset, step, rollout, replay, validate,
train, rank, promote, mutate checkpoints, tune profiles, or claim performance.

## Evidence Summary

M3015/M3016 support a narrow claim:

```text
M3015 produced complete, claim-safe diagnostic execution artifacts.
M3016 accepted the artifacts as complete and claim-safe.
M3015 preserved 16 M3006 task_source ids and 32 M3012 workload rows.
All 32 scheduled rows produced episode rows.
Failure rows: 0.
Actor contract: observation 72, action 3.
```

The diagnostic outcomes were strongly negative:

```text
success rows: 3
collision rows: 5
off_track terminations: 23
obstacle_collision terminations: 4
speed_too_low terminations: 2
blank termination_reason rows: 3
```

These numbers are useful for failure localization only. They are not a
validation result, repair-success result, driver-performance result, paper
result, current-sim verdict, high-fidelity readiness result, full-driver result,
finite-window-vs-GRU result, ranking result, promotion result, or self-ID result.

## Supported Claims

M3017 supports only these claims:

```text
M3015/M3016 artifacts are complete enough for a follow-up failure-localization route.
The new-source surface is not immediately suitable for validation or promotion interpretation.
The next route should preserve the 32-row denominator and classify failure modes before repair.
```

## Falsified Or Unsupported Claims

M3017 rejects these claims:

```text
driver performance improved
repair succeeded
M3015 validates the candidate checkpoint
M3015 ranks candidate versus parent
M3015 justifies winner selection or promotion
M3015 is paper evidence
M3015 changes the current-sim verdict
M3015 establishes high-fidelity readiness
M3015 decides finite-window-vs-GRU
M3015 advances full ideal driver completion
M3015 establishes level3 self-identification
```

## Failure Taxonomy Summary

The dominant observed diagnostic family is offtrack termination, with collision
and speed-too-low as secondary families. The current artifacts are not yet
organized enough to say whether failures are primarily profile-specific,
source-family-specific, task-family-specific, or shared across both candidate
and parent profiles.

That missing localization blocks a responsible repair decision.

## Public Gate Overfit Risk

Continuing directly to a repair, ranking, or promotion milestone would risk
optimizing against this freshly exposed 32-row diagnostic surface. The next
step must therefore be denominator-preserving failure localization, not tuning
or winner selection.

## Next Branch Decision

M3017 continues exactly once to:

```text
m3018-engineering-controller-route-a-post-residual-stop-new-source-failure-localization-materialization-preflight
```

M3018 must materialize failure-localization rows from existing M3015 artifacts
only. It may group by profile, task source, task family, source family,
termination family, collision flag, and success flag. It must not rerun
episodes, train, rank, promote, mutate checkpoints, tune profiles, validate,
or claim performance.

## Stop Conditions For The Next Route

M3018 must stop or route to synthesis if:

```text
it cannot preserve the 32-row denominator
it needs another rollout or profile/checkpoint mutation
it turns diagnostic counts into a performance verdict
it cannot distinguish source-specific and shared failure modes enough to select a bounded next route
```
