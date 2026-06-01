# M2316 Paper-Route Current-Sim Scenario Task-Family Metric Semantics Conflict Diagnosis Result Audit

- status: completed
- decision: `route_to_role_success_semantics_repair_design`
- manifest: `experiments/manifests/m2316-paper-route-current-sim-scenario-task-family-metric-semantics-conflict-diagnosis-result-audit.json`
- parent summary: `runs/m2315_paper_route_current_sim_scenario_task_family_metric_semantics_conflict_diagnosis/summary.json`
- parent role summary: `runs/m2315_paper_route_current_sim_scenario_task_family_metric_semantics_conflict_diagnosis/role_metric_semantics_summary.csv`
- parent scenario diagnosis: `runs/m2315_paper_route_current_sim_scenario_task_family_metric_semantics_conflict_diagnosis/scenario_metric_semantics_diagnosis.csv`
- reset/rollout/policy action in M2316: `false`
- training/replay/PPO in M2316: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Completeness Audit

M2315 is complete enough for result audit:

```text
result_class: current_sim_scenario_task_family_metric_semantics_conflict_diagnosis_pass
input_episode_count: 1080
input_scenario_support_label_count: 72
scenario_metric_semantics_row_count: 72
input_role_support_summary_count: 6
guardrail_violation_count: 0
```

M2315 did not run reset, rollout, policy action, measured execution, replay,
PPO, private holdout, ranking, or promotion.

## R0 Semantics Audit

R0 has decisive safe-stop evidence:

```text
r0_safe_stop_scenario_count: 12
r0_safe_stop_episode_count: 62
r0_aeb_safe_stop_episode_count: 60
r0_min_safe_stop_clearance_margin: 10.96082732487428
r0_mean_safe_stop_clearance_margin: 25.993928793681416
r0_max_safe_stop_clearance_margin: 43.58735902844862
```

Audit decision:

```text
R0_stable_avoidable: role_safe_stop_success_semantics_repair_required
```

Interpretation: for an AEB-feasible stable-avoidable role, stopping safely
before the obstacle with positive clearance is a valid support outcome. The
current obstacle-pass success semantics incorrectly counts those rows as
non-success. R0 must be repaired before any current-sim comparison, controller
family ranking, or training route that uses these role-family labels.

## Residual Support Audit

M2315 also reports:

```text
metric_conflict_scenario_count: 13
safe_stop_metric_conflict_scenario_count: 23
safe_stop_metric_conflict_episode_count: 92
residual_support_blocked_scenario_count: 18
```

Role labels:

```text
R0_stable_avoidable: role_safe_stop_success_semantics_repair_required
R1_aeb_infeasible_stable_aes: role_non_metric_conflict
R2_handling_limit_drift_capable_avoidance: role_support_redesign_candidate
R3_recovery_after_limit: role_support_redesign_candidate
R4_unavoidable_mitigation: role_support_redesign_candidate
R5_hidden_dynamics_robustness: role_support_redesign_candidate
```

R2-R5 are not interpreted as failed driver evidence. They remain scenario
support or semantics redesign candidates until the R0 safe-stop semantics repair
is implemented and the same M2313 artifacts are rescored.

## Route Decision

Route to:

```text
m2317-paper-route-current-sim-scenario-task-family-role-success-semantics-repair-design
```

M2317 should freeze a reusable role-success semantics contract before any code
implementation. The first required semantics repair is:

```text
R0 stable avoidable:
  success if obstacle-pass success is true
  OR termination_reason == speed_too_low with positive clearance,
     no collision, and no offtrack
```

M2317 should also define the artifact-only rescore and rerun boundary for the
M2318 implementation. It must not directly train, compare controller families,
promote checkpoints, or make paper-level/self-ID claims.

## Blocked Routes

Blocked:

```text
direct training from obstacle-pass-only success labels;
claiming R0 support-blocked;
controller-family ranking from M2313/M2315;
driver performance or paper-level claims;
finite-window vs GRU or level3 self-ID claims.
```

## Follow-Up

Pre-register:

```text
experiments/manifests/m2317-paper-route-current-sim-scenario-task-family-role-success-semantics-repair-design.json
```
