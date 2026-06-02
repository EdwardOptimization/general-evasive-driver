# M2345 Paper-Route Current-Sim Scenario Support Redesign Branch Synthesis

- status: completed
- synthesis decision: `continue`
- decision: `continue_to_dual_axis_redesign_calibration_design`
- manifest: `experiments/manifests/m2345-paper-route-current-sim-scenario-support-redesign-branch-synthesis.json`
- synthesis artifact: `docs/m2345-paper-route-current-sim-scenario-support-redesign-branch-synthesis.md`
- synthesis window: `M2338-M2344`
- reset/rollout/policy action in M2345: `false`
- measured execution in M2345: `false`
- training/replay/PPO in M2345: `false`
- support-policy ranking claim made: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

M2338 synthesized the residual task-quality branch and selected source mapping
over the 23 support-policy coverage gap rows:

```text
support-policy coverage gaps: 23
scenario/support redesign gaps: 12
R4 post-collision blocked: 12
metric edge rows: 1
```

M2340 source-mapped the 23 coverage rows:

```text
coverage_gap_row_count: 23
support_policy_coverage_materialization_candidate: 9
scenario_or_support_redesign_candidate: 14
unclassified_count: 0
guardrail_violation_count: 0
support-policy success across those 23 rows: 0
```

M2341 accepted M2340 and identified a larger redesign-related bucket:

```text
original M2336 redesign rows: 12
remapped M2340 redesign candidates: 14
combined redesign-related blocker: 26
secondary coverage-materialization bucket: 9
```

M2343 consolidated the redesign bucket:

```text
combined_redesign_related_row_count: 26
unique_redesign_scenario_count: 26
secondary_coverage_materialization_row_count: 9
duplicate_redesign_scenario_count: 0
needs_user_review_count: 0
guardrail_violation_count: 0
```

M2343/M2344 exposed the key blocker:

```text
geometry_timing_rebalance_candidate: 13
hidden_dynamics_range_rebalance_candidate: 13
```

The two source streams lean differently:

```text
original M2336 redesign rows:
  geometry/timing: 3
  hidden range: 9

remapped M2340 rows:
  geometry/timing: 10
  hidden range: 4
```

## Supported Claims

M2345 supports these bounded claims:

- The current-sim task-quality blocker is now more precise than "support gap":
  it is a 26-row redesign-related blocker plus a 9-row secondary coverage
  bucket.
- The 26 redesign-related rows are unique and source-mapped.
- Geometry/timing pressure and hidden-dynamics range pressure are both
  first-class blockers.
- A direct single-axis redesign branch would be under-justified because the
  route split is exactly 13/13 and the input sources disagree.
- Controller-family comparison remains blocked by scenario/task-quality work.

## Falsified Claims

M2345 falsifies or blocks these claims:

- The current-sim pack is ready for controller-family comparison.
- Support-policy coverage materialization alone is the dominant next route.
- Hidden-dynamics range alone is the dominant next route.
- Geometry/timing rebalance alone is the dominant next route.
- The 26-row blocker proves driver failure or self-identification failure.
- Scenario redesign has already been executed.
- This branch provides finite-window vs GRU, paper-level, or level3 self-ID
  evidence.

## Failure Taxonomy Summary

```text
scenario_sampling_failure:
  The dominant failure type. The pack contains 26 redesign-related rows split
  between geometry/timing and hidden-dynamics range pressures.

metric_artifact:
  Earlier R0 and R4 metric artifacts were repaired or bounded before this
  branch. No new metric-edge blocker dominates M2340-M2344.

objective_overfit:
  Prior training/repair work was blocked until task quality was clarified.
  M2338-M2345 deliberately avoid PPO or replay so controller evidence is not
  interpreted from unsupported scenario rows.
```

## Public Gate Overfit Risk

The public gate overfit risk is moderate.

The branch still analyzes the same current-sim role-family pack, but it changed
the evidence rather than repeatedly repairing one label:

```text
M2340:
  source-mapped coverage gaps and showed no support-policy successes.

M2343:
  consolidated 26 unique redesign-related rows.

M2344:
  detected an exact geometry-vs-hidden split and stopped direct single-axis
  local search.
```

The next route should therefore preserve both axes in a small redesign
calibration design instead of choosing one public slice to optimize.

## Paper-Route Axis Classification

```text
engineering driver performance:
  no new claim. No driver checkpoint is evaluated.

mechanism evidence for history dependence:
  no new support. No finite-window, GRU, wrong-history, reset-hidden, or
  zero-history comparison is run.

scenario/task-quality evidence:
  strong positive evidence. The branch identifies the dominant current-sim
  blocker as a dual-axis scenario/support redesign problem.

high-fidelity validation readiness:
  not ready. Current-sim task pack and controller set are not frozen.

workflow or complexity reduction:
  positive. Synthesis prevents a single-axis local search and turns the next
  step into a bounded dual-axis calibration design.
```

## Next Branch Decision

Decision:

```text
continue
```

New branch:

```text
paper_route_current_sim_dual_axis_redesign_calibration
```

Next milestone:

```text
m2346-paper-route-current-sim-dual-axis-redesign-calibration-design
```

M2346 should design a bounded dual-axis calibration plan that preserves both
blockers:

```text
G axis:
  geometry/timing rebalance candidates for geometry_timing rows.

H axis:
  hidden-dynamics range rebalance candidates for hidden_range rows.

GH axis:
  a minimal combined calibration option only if a row carries both geometry and
  hidden stress signals.

Secondary:
  keep the 9 coverage-materialization rows tracked but do not start support
  coverage materialization until the redesign calibration path is defined.
```

M2346 should not execute rollouts or modify the active benchmark pack. It
should define candidate transformations, output artifacts, and pass/fail
criteria for a later artifact materializer.

## Blocked Routes

Blocked:

```text
direct geometry-only rebalance;
direct hidden-range-only rebalance;
support-policy coverage materialization;
controller-family comparison;
support-policy ranking;
driver checkpoint promotion;
training or PPO repair;
finite-window vs GRU comparison;
level3 self-ID claim;
paper-level current-sim result.
```

## Follow-Up Manifest

```text
experiments/manifests/m2346-paper-route-current-sim-dual-axis-redesign-calibration-design.json
```
