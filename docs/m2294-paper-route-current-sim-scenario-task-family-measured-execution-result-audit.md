# M2294 Paper-Route Current-Sim Scenario Task-Family Measured Execution Result Audit

- status: completed
- synthesis_decision: `continue`
- decision: `scenario_task_family_measured_execution_audit_continue_to_failure_slice_diagnosis`
- manifest: `experiments/manifests/m2294-paper-route-current-sim-scenario-task-family-measured-execution-result-audit.json`
- parent result: `runs/m2293_paper_route_current_sim_scenario_task_family_measured_execution/summary.json`
- rerun/reset/rollout/policy action in M2294: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

M2290 made the role-family scenario pack reset-valid under the P0 actor
contract. M2292 froze the measured execution design. M2293 implemented and ran
the frozen 72 scenario spec x 15 selected checkpoint panel.

M2293 completeness:

```text
episode_count: 1080 / 1080
scenario_spec_count: 72 / 72
selected_checkpoint_count: 15 / 15
failure_count: 0
validation_failure_count: 0
metadata_missing_count: 0
metric_completeness_failure_count: 0
guardrail_violation_count: 0
label_mismatch_count: 0
```

M2293 global outcome:

```text
success_count: 69
success_rate: 0.06388888888888888
collision_count: 209
collision_rate: 0.1935185185185185
offtrack_count: 785
offtrack_rate: 0.7268518518518519
max_step_noncompletion_count: 7
max_step_noncompletion_rate: 0.006481481481481481
other_failure_count: 10
other_failure_rate: 0.009259259259259259
mean_min_clearance_margin: 6.802372067958403
min_min_clearance_margin: -0.3498040457660503
dominant_failure_mode: offtrack_dominated_failure
```

Role-family snapshot:

```text
R0_stable_avoidable:
  success_rate: 0.05555555555555555
  dominant_failure_mode: offtrack_dominated_failure

R1_aeb_infeasible_stable_aes:
  success_rate: 0.3277777777777778
  dominant_failure_mode: offtrack_dominated_failure

R2_handling_limit_drift_capable_avoidance:
  success_rate: 0.0
  dominant_failure_mode: offtrack_dominated_failure

R3_recovery_after_limit:
  success_rate: 0.0
  dominant_failure_mode: offtrack_dominated_failure

R4_unavoidable_mitigation:
  success_rate: 0.0
  dominant_failure_mode: collision_dominated_failure

R5_hidden_dynamics_robustness:
  success_rate: 0.0
  dominant_failure_mode: offtrack_dominated_failure
```

## Supported Claims

M2294 supports these bounded claims:

- The reset-valid current-sim scenario task-family pack is executable with the
  M2262 selected-checkpoint panel.
- The focused measured runner preserves metadata and claim-boundary guardrails.
- The current selected-checkpoint family is not ready for this six-role scenario
  pack; global success is low and failures are dominated by offtrack plus R4
  collision.
- The next useful evidence step is failure-slice diagnosis over existing M2293
  artifacts, not another blind training or ranking step.

## Falsified Claims

M2294 falsifies or blocks these claims:

- Reset-valid scenario generation is sufficient to demonstrate driver quality.
- The current M2262 selected checkpoints are strong across the full role-family
  scenario distribution.
- M2293 profile aggregates are ranking evidence.
- M2293 is paper-level benchmark evidence.
- M2293 is finite-window vs GRU evidence.
- M2293 is level3 self-identification evidence.

## Failure Taxonomy Summary

The M2293 failure is not an infrastructure or schema failure:

```text
validation_failure_count: 0
metadata_missing_count: 0
metric_completeness_failure_count: 0
guardrail_violation_count: 0
```

The observed failure class is behavioral/task-performance failure:

```text
global dominant_failure_mode: offtrack_dominated_failure
R4 dominant_failure_mode: collision_dominated_failure
```

The likely failure taxonomy for the next diagnosis is:

```text
behavior_regression_or_task_mismatch:
  current checkpoint family does not handle the new role-family task pack.

scenario_task_quality_risk:
  reset-validity does not yet imply a well-shaped training/evaluation curriculum.

metric_artifact risk:
  profile aggregates exist, but they must not be interpreted as ranking before
  denominator-backed diagnosis.
```

## Public Gate Overfit Risk

Execution-completeness overfit risk is low: M2293 measured a full 1080-cell
panel with balanced role-family and profile coverage.

Performance-interpretation overfit risk is high:

- the scenario pack is public and newly materialized;
- the checkpoint family is inherited from M2262 rather than trained for this
  task pack;
- profile aggregates can tempt premature ranking;
- M2293 did not run private holdout, fresh seeds, history ablations, or
  denominator-backed finite-window/GRU comparisons.

Therefore the next step must diagnose failure structure before any repair,
ranking, or paper-route claim.

## Next Branch Decision

Decision:

```text
continue
```

The branch should continue, but only as artifact-only failure-slice diagnosis:

```text
m2295-paper-route-current-sim-scenario-task-family-failure-slice-diagnosis-implementation
```

M2295 should consume only existing M2293 artifacts and produce slice-level
diagnostics across:

```text
role_family
scenario_family_id
sampled_obstacle_label
obstacle_longitudinal_timing_bucket
obstacle_lateral_offset_bucket
hidden_dynamics_bucket
profile_name
profile_seed
outcome_bucket
termination_reason
```

M2295 should not rerun rollout, train, rank profiles, or change the scenario
pack. Its purpose is to decide whether the next route is offtrack containment,
collision/mitigation repair, scenario-task reshaping, or branch-level stop/pivot.

## Follow-Up

Pre-registered:

```text
experiments/manifests/m2295-paper-route-current-sim-scenario-task-family-failure-slice-diagnosis-implementation.json
```
