# M2343 Paper-Route Current-Sim Scenario Support Redesign Consolidation Implementation

- status: completed
- result_class: `current_sim_scenario_support_redesign_consolidation_pass`
- manifest: `experiments/manifests/m2343-paper-route-current-sim-scenario-support-redesign-consolidation-implementation.json`
- parent design: `docs/m2342-paper-route-current-sim-scenario-support-redesign-consolidation-design.md`
- implementation: `src/autodrift/paper_route_current_sim_scenario_support_redesign_consolidation.py`
- tests: `tests/test_paper_route_current_sim_scenario_support_redesign_consolidation.py`
- output: `runs/m2343_paper_route_current_sim_scenario_support_redesign_consolidation/summary.json`
- reset/rollout/policy action in M2343: `false`
- measured execution in M2343: `false`
- training/replay/PPO in M2343: `false`
- support-policy ranking claim made: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Command

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_scenario_support_redesign_consolidation \
  --rescore-dir runs/m2336_paper_route_current_sim_role_stratified_residual_support_rescore \
  --residual-dir runs/m2321_paper_route_current_sim_scenario_task_family_residual_support_audit \
  --source-mapping-dir runs/m2340_paper_route_current_sim_support_coverage_gap_source_mapping \
  --output-dir runs/m2343_paper_route_current_sim_scenario_support_redesign_consolidation
```

Focused validation:

```text
PYTHONPATH=src python -m pytest tests/test_paper_route_current_sim_scenario_support_redesign_consolidation.py -q
1 passed

python -m compileall -q src tests
passed
```

## Output Artifacts

```text
runs/m2343_paper_route_current_sim_scenario_support_redesign_consolidation/summary.json
runs/m2343_paper_route_current_sim_scenario_support_redesign_consolidation/consolidated_redesign_rows.csv
runs/m2343_paper_route_current_sim_scenario_support_redesign_consolidation/secondary_coverage_materialization_rows.csv
runs/m2343_paper_route_current_sim_scenario_support_redesign_consolidation/redesign_axis_summary.csv
runs/m2343_paper_route_current_sim_scenario_support_redesign_consolidation/redesign_route_summary.csv
runs/m2343_paper_route_current_sim_scenario_support_redesign_consolidation/redesign_source_summary.csv
runs/m2343_paper_route_current_sim_scenario_support_redesign_consolidation/claim_boundary.csv
```

## Result Summary

M2343 consolidates the redesign-related bucket cleanly:

```text
original_redesign_gap_count: 12
remapped_coverage_redesign_candidate_count: 14
combined_redesign_related_row_count: 26
unique_redesign_scenario_count: 26
secondary_coverage_materialization_row_count: 9
duplicate_redesign_scenario_count: 0
needs_user_review_count: 0
guardrail_violation_count: 0
```

Recommended redesign route split:

```text
geometry_timing_rebalance_candidate: 13
hidden_dynamics_range_rebalance_candidate: 13
role_semantics_or_success_metric_review_candidate: 0
support_policy_after_redesign_candidate: 0
needs_user_review: 0
```

Theme split:

```text
collision_timing_pressure: 5
offtrack_geometry_pressure: 8
hidden_dynamics_stress: 11
hidden_dynamics_robustness_task_quality: 2
```

Source split:

```text
original_m2336_redesign_gap:
  rows: 12
  geometry/timing: 3
  hidden-dynamics range: 9

remapped_m2340_coverage_redesign_candidate:
  rows: 14
  geometry/timing: 10
  hidden-dynamics range: 4
```

Axis highlights:

```text
role_family:
  R2: 8 rows, 4 geometry/timing, 4 hidden range
  R3: 7 rows, 3 geometry/timing, 4 hidden range
  R5: 11 rows, 6 geometry/timing, 5 hidden range

timing:
  late_close: 10 rows, 9 geometry/timing, 1 hidden range
  early_far: 8 rows, 1 geometry/timing, 7 hidden range
  mid: 8 rows, 3 geometry/timing, 5 hidden range

lateral:
  centerline: 10 rows, 3 geometry/timing, 7 hidden range
  left_offset: 9 rows, 5 geometry/timing, 4 hidden range
  right_offset: 7 rows, 5 geometry/timing, 2 hidden range

dominant_failure:
  collision_dominated_failure: 13 rows, 5 geometry/timing, 8 hidden range
  offtrack_dominated_failure: 12 rows, 8 geometry/timing, 4 hidden range
  mixed_failure: 1 row, 0 geometry/timing, 1 hidden range
```

## Interpretation

M2343 makes the task-quality blocker sharper:

- The 26 redesign-related rows are real and deduplicated.
- The redesign problem is evenly split between geometry/timing pressure and
  hidden-dynamics range pressure.
- The original M2336 redesign rows lean hidden-dynamics range, while the
  remapped M2340 rows lean geometry/timing.
- The 9 secondary coverage-materialization rows remain tracked, but they are
  not the dominant next blocker.

This result does not tell us how to edit the scenario pack yet. It only says
that a single direct fix would be risky: geometry/timing and hidden-dynamics
range are both first-class blockers.

## Claim Boundary

Allowed claim:

```text
M2343 materializes a 26-row artifact-only scenario/support redesign
consolidation with a 13/13 geometry-vs-hidden split.
```

Blocked claims:

```text
scenario redesign executed;
support-policy ranking;
controller comparison readiness;
residual support solved;
paper-level evidence;
finite-window vs GRU conclusion;
level3 self-identification evidence.
```

## Follow-Up

M2344 should audit the 13/13 route split before choosing between geometry/timing
rebalance, hidden-dynamics range rebalance, or branch synthesis:

```text
experiments/manifests/m2344-paper-route-current-sim-scenario-support-redesign-consolidation-result-audit.json
```
