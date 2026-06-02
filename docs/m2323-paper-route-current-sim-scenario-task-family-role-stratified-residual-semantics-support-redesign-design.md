# M2323 Paper-Route Current-Sim Scenario Task-Family Role-Stratified Residual Semantics/Support Redesign Design

- status: completed
- result_class: `role_stratified_residual_redesign_design_admit_artifact_only_implementation`
- manifest: `experiments/manifests/m2323-paper-route-current-sim-scenario-task-family-role-stratified-residual-semantics-support-redesign-design.json`
- parent audit: `docs/m2322-paper-route-current-sim-scenario-task-family-residual-support-audit-result-audit.md`
- parent residual rows: `runs/m2321_paper_route_current_sim_scenario_task_family_residual_support_audit/residual_scenario_rows.csv`
- reset/rollout/policy action in M2323: `false`
- training/replay/PPO in M2323: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Design Decision

M2323 freezes a role-stratified artifact-only implementation route. The next
step must materialize diagnostic redesign rows, not run policies or rank
controller families.

The design separates three residual meanings:

```text
R4_unavoidable_mitigation:
  mitigation semantics/support redesign.

R2/R3/R5 support_mixed:
  support-policy coverage audit candidate.

R2/R3/R5 support_blocked:
  scenario-or-support redesign candidate.
```

The single R3 `metric_conflict` row remains a diagnostic edge case and should be
kept out of broad metric repair unless it recurs in a source-diverse refresh.

## R4 Mitigation Semantics Requirements

R4 is not ordinary obstacle-passage avoidance. It must not be scored with the
same success semantics as R0-R3/R5 until mitigation-specific metrics exist.

Allowed R4 mitigation questions:

```text
Did the controller reduce collision severity?
Did it avoid road departure while mitigating?
Did it reduce off-track overshoot?
Did it keep the vehicle recoverable after the unavoidable event?
Did it avoid turning a low-severity impact into a worse offtrack/collision mode?
```

Required mitigation metric fields for a future measured execution:

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

Current M2318/M2321 artifacts do not contain those severity-specific fields.
They only contain coarse proxies:

```text
collision
outcome_bucket
termination_reason
min_clearance_margin
max_off_track_overshoot
time_to_first_off_track_s
high_sideslip_fraction
action_rate_mean
return
```

Therefore M2324 must mark R4 rows as `mitigation_metric_availability_gap` unless
all required severity fields are present. It may still materialize the R4 rows
and proxy columns, but it must not claim mitigation performance.

## R2/R3/R5 Coverage-vs-Redesign Requirements

For non-R4 residuals, the implementation should produce one row per residual
scenario with a non-ranking design route:

```text
support_policy_coverage_candidate:
  some diagnostic support exists, but the current AEB/AES/envelope-AES support
  set is too weak or too sparse to support controller-family comparison.

scenario_or_support_redesign_candidate:
  no current support policy provides enough support; the row needs a scenario
  feasibility audit, richer support policy, local teacher, or task redesign
  before it can be used for paper-level controller comparison.

metric_semantics_audit_candidate:
  keep as an edge diagnostic unless source-diverse recurrence appears.
```

The implementation must preserve axis detail:

```text
role_family
support_label
dominant_failure_mode
hidden_dynamics_bucket
obstacle_longitudinal_timing_bucket
obstacle_lateral_offset_bucket
sampled_obstacle_label
```

## M2324 Artifact-Only Implementation

M2324 should implement a runner:

```text
src/autodrift/paper_route_current_sim_scenario_task_family_role_stratified_residual_redesign.py
```

Inputs:

```text
runs/m2321_paper_route_current_sim_scenario_task_family_residual_support_audit/residual_scenario_rows.csv
runs/m2318_paper_route_current_sim_scenario_task_family_role_success_semantics_repair/episode_rows_rescored.csv
```

Outputs:

```text
summary.json
role_stratified_residual_rows.csv
r4_mitigation_metric_availability.csv
r2_r3_r5_coverage_redesign_rows.csv
axis_route_summary.csv
claim_boundary.csv
run_state.json
```

Guardrails:

```text
environment_reset_started: false
environment_rollout_started: false
policy_action_executed: false
measured_rollout_started: false
training_started: false
replay_started: false
ppo_used: false
support_policy_ranking_claim_made: false
winner_selected: false
paper_level_claim_made: false
finite_window_vs_gru_conclusion_made: false
level3_self_id_claim_made: false
residual_support_solved_claim_made: false
```

Expected counts from M2321:

```text
input_residual_scenario_count: 48
R4 mitigation rows: 12
R2/R3/R5 coverage rows: 23
R2/R3/R5 redesign rows: 12
metric edge rows: 1
```

## Claim Boundary

Allowed claim:

```text
M2323 freezes a non-ranking role-stratified residual redesign route.
```

Blocked claims:

```text
mitigation performance is measured;
R4 is solved;
R2/R3/R5 are ready for controller ranking;
support policies are ranked;
driver performance improves;
paper-level current-sim evidence is complete;
finite-window vs GRU is decided;
level3 self-identification is shown.
```

## Follow-Up Manifest

```text
experiments/manifests/m2324-paper-route-current-sim-scenario-task-family-role-stratified-residual-redesign-implementation.json
```
