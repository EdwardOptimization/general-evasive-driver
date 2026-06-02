# M2325 Paper-Route Current-Sim Scenario Task-Family Role-Stratified Residual Redesign Result Audit

- status: completed
- result_class: `role_stratified_residual_redesign_result_accepted_route_to_r4_mitigation_metric_instrumentation_design`
- manifest: `experiments/manifests/m2325-paper-route-current-sim-scenario-task-family-role-stratified-residual-redesign-result-audit.json`
- parent result: `runs/m2324_paper_route_current_sim_scenario_task_family_role_stratified_residual_redesign/summary.json`
- parent metric availability: `runs/m2324_paper_route_current_sim_scenario_task_family_role_stratified_residual_redesign/r4_mitigation_metric_availability.csv`
- reset/rollout/policy action in M2325: `false`
- training/replay/PPO in M2325: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Audit Result

M2324 is accepted as a complete artifact-only role-stratified residual redesign
materialization:

```text
result_class: current_sim_scenario_task_family_role_stratified_residual_redesign_pass
role_stratified_residual_row_count: 48
R4 mitigation rows: 12
R2/R3/R5 coverage rows: 23
R2/R3/R5 redesign rows: 12
metric edge rows: 1
guardrail_violation_count: 0
```

M2325 accepts the R4 mitigation metric availability gap:

```text
r4_mitigation_metric_availability_gap: true
r4_available_required_mitigation_metric_count: 0
r4_missing_required_mitigation_metric_count: 8
```

Missing required R4 severity fields:

```text
impact_speed_mps
delta_v_at_impact_mps
time_to_collision_s
collision_angle_or_side
post_event_speed_mps
post_event_yaw_rate_abs
post_event_offtrack_overshoot
recoverability_window_success
```

## Interpretation

The current-sim scenario task-family route cannot make a paper-level statement
about unavoidable mitigation until the measured execution artifacts can record
mitigation severity. Coarse proxy fields such as collision, termination reason,
minimum clearance, offtrack overshoot, sideslip fraction, action rate, and return
are useful diagnostics, but they do not establish mitigation performance.

The R2/R3/R5 coverage-vs-redesign artifacts remain valid and should be retained,
but R4 instrumentation is the higher-priority blocker because without it one
role family has no admissible role metric.

## Accepted Claim

Allowed claim:

```text
M2324 materialized role-stratified residual redesign artifacts and showed that
R4 mitigation severity instrumentation is missing from current artifacts.
```

Blocked claims:

```text
mitigation performance measured;
R4 mitigation solved;
support-policy or controller-family ranking;
winner selection;
paper-level current-sim evidence;
finite-window vs GRU conclusion;
level3 self-identification evidence.
```

## Next Route

M2325 selects a non-ranking design milestone:

```text
m2326-paper-route-current-sim-r4-mitigation-metric-instrumentation-design
```

The design must map each required field to a concrete simulator or measured-run
source without changing the actor observation contract, reward, controller
behavior, or training objective.

M2326 must also keep R2/R3/R5 artifacts frozen as pending scenario/support
redesign material, not as ranking evidence.

## Follow-Up Manifest

```text
experiments/manifests/m2326-paper-route-current-sim-r4-mitigation-metric-instrumentation-design.json
```
