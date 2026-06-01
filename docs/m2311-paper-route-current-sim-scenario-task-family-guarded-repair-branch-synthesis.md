# M2311 Paper-Route Current-Sim Scenario Task-Family Guarded-Repair Branch Synthesis

- status: completed
- synthesis decision: `pivot`
- decision: `pivot_to_scenario_task_family_feasibility_calibration`
- manifest: `experiments/manifests/m2311-paper-route-current-sim-scenario-task-family-guarded-repair-branch-synthesis.json`
- synthesis artifact: `docs/m2311-paper-route-current-sim-scenario-task-family-guarded-repair-branch-synthesis.md`
- synthesis window: `M2300-M2310`
- reset/rollout/policy action in M2311: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

M2300 continued from target/guardrail materialization into guarded repair with
a clear non-ranking repair gate:

```text
offtrack target slices: 20
collision guardrail slices: 11
required direction:
  global offtrack decrease;
  global collision non-increase;
  target slice offtrack non-increase;
  guardrail slice collision non-increase.
```

M2301-M2303 designed and materialized a 15-config guarded-v2 repair matrix.
M2304 then executed all 15 training runs cleanly:

```text
completed_run_count: 15
failed_run_count: 0
candidate_eval_count: 120
selected_checkpoint_count: 15
selected_beats_final_count: 10 / 15
selected_profile_floor_pass_count: 0
selected_readiness_floor_pass_count: 5 / 15
guardrail_violation_count: 0
```

M2305 correctly refused to interpret selected checkpoint metrics as repair
success and routed to measured execution. M2307 executed the same 1080-episode
role-family panel as M2293:

```text
M2293 success/offtrack/collision: 69 / 785 / 209
M2307 success/offtrack/collision: 68 / 786 / 218
delta: -1 / +1 / +9
mean_min_clearance_margin_delta: -0.341165
```

M2309 materialized the full target/guardrail slice diagnosis:

```text
slice_delta_row_count: 31
repair_gate_pass: false
offtrack_target_nonincrease/increase: 9 / 20, 11 / 20
collision_guardrail_nonincrease/increase: 4 / 11, 7 / 11
```

M2310 accepted the result as broad guarded-v2 repair failure and blocked another
same-support scalar repair run.

## Supported Claims

M2311 supports these bounded claims:

- The guarded-v2 branch was executed cleanly enough to evaluate its result.
- Training completeness and candidate selection are not enough; the selected
  checkpoints failed the measured target/guardrail gate.
- The M2298 target/guardrail pack is useful as a fail-closed diagnostic: it
  caught a global and slice-level repair regression.
- The branch has reached the local-search stop condition. Continuing with
  another reward coefficient, another same-family selected-checkpoint run, or a
  profile ranking pass would not change the evidence axis.
- The current blocker is scenario/task-family feasibility and support
  calibration, not another immediate PPO or scalar reward repair.

## Falsified Claims

M2311 falsifies or blocks these claims:

- Guarded-v2 same-support scalar repair fixes the current 72-spec role-family
  panel.
- Selected checkpoint improvement over final checkpoints implies measured
  task-family repair.
- Global success/offtrack/collision can be inferred from training-time selected
  checkpoint metrics.
- The current panel is ready for controller-family ranking, winner selection,
  finite-window vs GRU conclusions, paper-level claims, or level3
  self-identification.
- More local tuning on the same M2298 repair support is justified before a
  branch synthesis or new evidence axis.

## Failure Taxonomy Summary

Primary failure types:

```text
behavior_regression:
  M2307 worsened global offtrack and collision versus M2293.

scenario_sampling_failure:
  the role-family pack remains offtrack dominated and exposes collision
  guardrail regressions after repair.

objective_overfit:
  repair pressure and selected-checkpoint criteria did not transfer to the
  target/guardrail measured panel.

metric_artifact:
  candidate eval metrics and selected-beats-final counts looked useful but did
  not predict repair success.

seed_fragility:
  15 selected checkpoints executed cleanly, but none produced a profile-floor
  pass, and the panel result regressed globally.
```

## Public Gate Overfit Risk

The public gate overfit risk is high.

The M2298 target/guardrail pack has now been used for design, config
materialization, training execution, selected-checkpoint measured execution,
slice diagnosis, and result audit. If the project keeps tuning on this same
support, the workflow will become a gate-passing loop rather than a research
system that explains the failure.

The next branch must change the question from:

```text
Can this scalar guarded repair reduce public offtrack while preserving collision?
```

to:

```text
Is the current role-family task pack feasible, calibrated, and supportable
enough to be a fair training/evaluation target?
```

## Paper-Route Axis Classification

```text
engineering driver performance:
  negative diagnostic. The current selected-checkpoint family is far below
  role-family readiness and guarded-v2 repair regressed measured outcomes.

mechanism evidence for history dependence:
  no new support. M2311 runs no wrong-history, reset-hidden, zero-history,
  finite-window, or GRU comparison tests.

scenario/task-quality evidence:
  strong negative. The current task pack exposes broad failures, but the branch
  does not yet separate policy weakness from task infeasibility or poor
  calibration.

high-fidelity validation readiness:
  not ready. The current-sim task verdict and benchmark pack are not frozen.

workflow or complexity reduction:
  positive. The branch closes same-support guarded-v2 repair and forces a new
  evidence axis.
```

## Next Branch Decision

Decision:

```text
pivot
```

New branch:

```text
paper_route_current_sim_scenario_task_family_feasibility_calibration
```

Next milestone:

```text
m2312-paper-route-current-sim-scenario-task-family-feasibility-calibration-design
```

M2312 should design, not execute, a feasibility/support calibration route for
the 72-spec role-family pack. The route should determine whether failures are
primarily caused by:

```text
task infeasibility or over-aggressive geometry;
scenario support imbalance;
missing or weak reference/support policies;
current actor weakness under otherwise feasible tasks;
metric definitions that over-penalize recoverable maneuvers;
collision/offtrack tradeoffs that need role-specific constraints.
```

The branch may use reference/support policies only as diagnostic support bounds,
not for controller-family ranking or winner selection.

## Blocked Routes

Blocked:

```text
another guarded-v2 scalar reward tweak;
another same-support selected-checkpoint repair run;
profile ranking from M2307/M2309;
lowering target/guardrail thresholds to make M2307 pass;
controller-family comparison before feasibility calibration;
finite-window vs GRU conclusion;
paper-level result;
level3 self-identification claim;
high-fidelity validation as primary route.
```

## Follow-Up

Pre-register:

```text
experiments/manifests/m2312-paper-route-current-sim-scenario-task-family-feasibility-calibration-design.json
```
