# M2340 Paper-Route Current-Sim Support Coverage Gap Source Mapping Implementation

- status: completed
- result_class: `current_sim_support_coverage_gap_source_mapping_pass`
- manifest: `experiments/manifests/m2340-paper-route-current-sim-support-coverage-gap-source-mapping-implementation.json`
- parent design: `docs/m2339-paper-route-current-sim-support-coverage-gap-source-mapping-design.md`
- implementation: `src/autodrift/paper_route_current_sim_support_coverage_gap_source_mapping.py`
- tests: `tests/test_paper_route_current_sim_support_coverage_gap_source_mapping.py`
- output: `runs/m2340_paper_route_current_sim_support_coverage_gap_source_mapping/summary.json`
- reset/rollout/policy action in M2340: `false`
- measured execution in M2340: `false`
- training/replay/PPO in M2340: `false`
- support-policy ranking claim made: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Command

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_support_coverage_gap_source_mapping \
  --rescore-dir runs/m2336_paper_route_current_sim_role_stratified_residual_support_rescore \
  --residual-dir runs/m2321_paper_route_current_sim_scenario_task_family_residual_support_audit \
  --support-dir runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration \
  --output-dir runs/m2340_paper_route_current_sim_support_coverage_gap_source_mapping
```

Focused validation:

```text
PYTHONPATH=src python -m pytest tests/test_paper_route_current_sim_support_coverage_gap_source_mapping.py -q
2 passed

python -m compileall -q src tests
passed
```

## Output Artifacts

```text
runs/m2340_paper_route_current_sim_support_coverage_gap_source_mapping/summary.json
runs/m2340_paper_route_current_sim_support_coverage_gap_source_mapping/coverage_gap_source_rows.csv
runs/m2340_paper_route_current_sim_support_coverage_gap_source_mapping/coverage_gap_axis_summary.csv
runs/m2340_paper_route_current_sim_support_coverage_gap_source_mapping/coverage_gap_support_policy_summary.csv
runs/m2340_paper_route_current_sim_support_coverage_gap_source_mapping/coverage_gap_recommended_route_summary.csv
runs/m2340_paper_route_current_sim_support_coverage_gap_source_mapping/claim_boundary.csv
```

## Result Summary

M2340 processes exactly the M2336 support-policy coverage gap bucket:

```text
coverage_gap_row_count: 23
target_coverage_gap_row_count: 23
role_count: 3
role_counts:
  R2_handling_limit_drift_capable_avoidance: 7
  R3_recovery_after_limit: 8
  R5_hidden_dynamics_robustness: 8
source_signature_count: 23
max_source_signature_share: 0.043478260869565216
unclassified_count: 0
guardrail_violation_count: 0
```

Recommended route split:

```text
support_policy_coverage_materialization_candidate: 9
scenario_or_support_redesign_candidate: 14
metric_edge_audit_candidate: 0
needs_user_review: 0
```

Role split:

```text
R2:
  coverage materialization: 4
  scenario/support redesign: 3

R3:
  coverage materialization: 4
  scenario/support redesign: 4

R5:
  coverage materialization: 1
  scenario/support redesign: 7
```

Key axis signals:

```text
hidden_dynamics_bucket:
  slow_steer_actuator: 9 rows, 5 coverage / 4 redesign
  low_mu: 6 rows, 3 coverage / 3 redesign
  tire_stiffness_shift: 4 rows, 1 coverage / 3 redesign
  nominal: 2 rows, 0 coverage / 2 redesign
  weak_brake: 2 rows, 0 coverage / 2 redesign

timing:
  early_far: 8 rows, 4 coverage / 4 redesign
  mid: 8 rows, 4 coverage / 4 redesign
  late_close: 7 rows, 1 coverage / 6 redesign

lateral:
  centerline: 9 rows, 6 coverage / 3 redesign
  left_offset: 7 rows, 1 coverage / 6 redesign
  right_offset: 7 rows, 2 coverage / 5 redesign

dominant_failure:
  collision_dominated_failure: 13 rows, 8 coverage / 5 redesign
  offtrack_dominated_failure: 10 rows, 1 coverage / 9 redesign
```

Support-policy aggregates are diagnostic only and do not rank policies:

```text
aeb: 23 scenarios, 115 episodes, success/collision/offtrack: 0 / 85 / 29
aes: 23 scenarios, 115 episodes, success/collision/offtrack: 0 / 72 / 43
envelope_aes: 23 scenarios, 115 episodes, success/collision/offtrack: 0 / 10 / 82
```

The important interpretation is that none of these 23 rows has support-policy
success evidence in the M2313 diagnostic panel. The 9 coverage-materialization
rows are routed that way because support policies fail in different modes,
meaning the panel is under-materialized rather than globally blocked. The 14
redesign rows fail in shared dominant modes and are more likely scenario/support
redesign blockers.

## Claim Boundary

Allowed claim:

```text
M2340 materializes an artifact-only source map for the 23 support-policy
coverage gap rows.
```

Blocked claims:

```text
support-policy ranking;
controller comparison readiness;
residual support solved;
paper-level evidence;
finite-window vs GRU conclusion;
level3 self-identification evidence.
```

## Follow-Up

M2341 should audit the M2340 result before any coverage materialization or
scenario redesign branch:

```text
experiments/manifests/m2341-paper-route-current-sim-support-coverage-gap-source-mapping-result-audit.json
```
