# M2300 Paper-Route Current-Sim Scenario Task-Family Guarded-Repair Branch Synthesis

- status: completed
- synthesis_decision: `continue`
- decision: `continue_to_guarded_repair_design_with_new_evidence_pressure`
- manifest: `experiments/manifests/m2300-paper-route-current-sim-scenario-task-family-guarded-repair-branch-synthesis.json`
- evidence window: `M2294-M2299`
- reset/rollout/policy action in M2300: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

M2294 accepted the first complete scenario task-family measured-execution panel.
The panel was complete but weak:

```text
episodes: 1080 / 1080
success_rate: 0.06388888888888888
offtrack_rate: 0.7268518518518519
collision_rate: 0.1935185185185185
dominant_failure_mode: offtrack_dominated_failure
metadata_missing_count: 0
metric_completeness_failure_count: 0
guardrail_violation_count: 0
```

M2295 reproduced the M2293 global counts and diagnosed failure slices without
rerun. The strongest route was offtrack-primary with collision guardrails:

```text
termination_reason=off_track:
  offtrack_count: 785

outcome_bucket=off_track_noncollision_noncompletion:
  offtrack_count: 785

outcome_bucket=collision_failure:
  collision_count: 209

termination_reason=obstacle_collision:
  collision_count: 208
```

M2298 converted the diagnosis into an explicit target/guardrail pack:

```text
offtrack_target_slice_count: 20
collision_guardrail_slice_count: 11
profile_target_slice_count: 0
profile_guardrail_slice_count: 0
repair_gate_spec_exists: true
```

M2299 accepted that pack and routed to guarded repair. M2300 was required
because the local-search guard correctly blocked another design-only milestone
without synthesis.

## Supported Claims

M2300 supports these bounded claims:

- The current-sim role-family scenario pack is reset-valid and execution-ready.
- The M2262 selected-checkpoint family is not adequate for the 72-spec
  role-family panel.
- Offtrack is the primary repair target; collision is a mandatory guardrail.
- The target/guardrail pack is broad enough to justify a guarded repair design:
  20 non-profile offtrack target slices and 11 non-profile collision guardrail
  slices.
- Profile axes are diagnostic-only and must not drive target selection,
  ranking, or tuning.

## Falsified Claims

M2300 falsifies or blocks these claims:

- Reset-valid scenario generation alone is enough for driver quality evidence.
- The current selected-checkpoint family is ready for paper-level evaluation.
- The M2293 profile aggregates can rank controller families.
- A direct broad reward/PPO repair should start before guarded target and
  collision constraints are frozen.
- This branch provides finite-window vs GRU evidence or level3 self-ID evidence.

## Failure Taxonomy Summary

The branch no longer looks like a data-schema or reset-sampling failure:

```text
M2293 validation_failure_count: 0
M2293 metadata_missing_count: 0
M2293 metric_completeness_failure_count: 0
M2293 guardrail_violation_count: 0
M2298 profile_target_slice_count: 0
M2298 profile_guardrail_slice_count: 0
```

The active failure is behavioral/task-performance:

```text
primary failure: offtrack_dominated_failure
secondary guardrail: collision_failure
```

Relevant taxonomy:

```text
behavior_regression:
  the current selected checkpoints do not handle the stronger role-family pack.

objective_overfit:
  prior scalar offtrack/corridor repair improved some local slices but did not
  solve aggregate task quality.

metric_artifact:
  profile aggregates and public target slices can be misread as ranking or
  paper evidence.

scenario_sampling_failure:
  currently resolved for reset/execution, but future repair must preserve the
  1080-episode denominator.
```

## Public Gate Overfit Risk

The overfit risk is medium.

The evidence is stronger than a singleton public proof row because M2298 targets
span role, label, timing, lateral, hidden-dynamics, outcome, and termination
axes. But all targets and guardrails still come from the public M2293 panel.
Therefore future repair must not tune to profile axes or declare success from
one slice improvement.

The next repair route must require:

```text
global offtrack reduction;
target-slice offtrack reduction or hold;
global collision non-increase;
guardrail-slice collision non-increase;
1080/1080 execution completeness;
no profile-specific target selection;
no ranking or paper-level claim.
```

## Paper-Route Consistency

This synthesis advances only:

```text
scenario/task-quality evidence
workflow or complexity reduction
```

It does not advance:

```text
mechanism evidence for history dependence
finite-window vs GRU comparison
level3 self-identification
high-fidelity validation readiness
```

This is consistent with the governing plans:

- self-identification remains a bounded hypothesis, not a default conclusion;
- finite-window/current-response may still be the engineering winner later;
- high-fidelity validation should wait until the current-sim task verdict and
  benchmark pack are stable.

## Next Branch Decision

Decision:

```text
continue
```

Continue only to guarded repair design:

```text
m2301-paper-route-current-sim-scenario-task-family-guarded-repair-design
```

M2301 must design the repair route, not execute it. It must freeze allowed
repair knobs, target gates, guardrail gates, and the next implementation route.
It should also force the next implementation to produce new measurable evidence
quickly, not another long chain of process-only milestones.

## Follow-Up

Pre-registered:

```text
experiments/manifests/m2301-paper-route-current-sim-scenario-task-family-guarded-repair-design.json
```
