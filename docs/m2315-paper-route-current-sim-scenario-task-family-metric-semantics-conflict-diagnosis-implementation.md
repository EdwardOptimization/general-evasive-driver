# M2315 Paper-Route Current-Sim Scenario Task-Family Metric Semantics Conflict Diagnosis Implementation

- status: completed
- result_class: `current_sim_scenario_task_family_metric_semantics_conflict_diagnosis_pass`
- manifest: `experiments/manifests/m2315-paper-route-current-sim-scenario-task-family-metric-semantics-conflict-diagnosis-implementation.json`
- summary: `runs/m2315_paper_route_current_sim_scenario_task_family_metric_semantics_conflict_diagnosis/summary.json`
- runner: `src/autodrift/paper_route_current_sim_scenario_task_family_metric_semantics_conflict_diagnosis.py`
- focused tests: `tests/test_paper_route_current_sim_scenario_task_family_metric_semantics_conflict_diagnosis.py`
- parent episode rows: `runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/episode_rows.csv`
- parent support labels: `runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/scenario_support_labels.csv`
- reset/rollout/policy action in M2315: `false`
- training/replay/PPO in M2315: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Command

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_scenario_task_family_metric_semantics_conflict_diagnosis \
  --episode-rows runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/episode_rows.csv \
  --scenario-support-labels runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/scenario_support_labels.csv \
  --role-support-summary runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/role_support_summary.csv \
  --output-dir runs/m2315_paper_route_current_sim_scenario_task_family_metric_semantics_conflict_diagnosis \
  --next-blocker m2316-paper-route-current-sim-scenario-task-family-metric-semantics-conflict-diagnosis-result-audit
```

## Artifact Completeness

M2315 is artifact-only and complete:

```text
input_episode_count: 1080
input_scenario_support_label_count: 72
scenario_metric_semantics_row_count: 72
input_role_support_summary_count: 6
guardrail_violation_count: 0
```

Written artifacts:

```text
summary.json
safe_stop_metric_conflict_rows.csv
scenario_metric_semantics_diagnosis.csv
metric_conflict_scenarios.csv
residual_support_blocked_scenarios.csv
role_metric_semantics_summary.csv
claim_boundary.csv
run_state.json
```

## Metric Semantics Result

M2315 separates safe-stop metric conflicts from residual support-blocked
scenarios:

```text
metric_conflict_scenario_count: 13
safe_stop_metric_conflict_scenario_count: 23
safe_stop_metric_conflict_episode_count: 92
residual_support_blocked_scenario_count: 18
```

R0 is the key semantics repair target:

```text
r0_safe_stop_scenario_count: 12
r0_safe_stop_episode_count: 62
r0_aeb_safe_stop_episode_count: 60
r0_min_safe_stop_clearance_margin: 10.96082732487428
r0_mean_safe_stop_clearance_margin: 25.993928793681416
r0_max_safe_stop_clearance_margin: 43.58735902844862
```

Interpretation: all R0 scenarios have safe-stop evidence, and the AEB support
policy safely stops before the obstacle with positive clearance. The current
obstacle-pass success semantics therefore misclassify a valid R0 safety outcome
as non-success. R0 should not be treated as support-blocked.

## Role Diagnosis

Role labels from `role_metric_semantics_summary.csv`:

```text
R0_stable_avoidable: role_safe_stop_success_semantics_repair_required
R1_aeb_infeasible_stable_aes: role_non_metric_conflict
R2_handling_limit_drift_capable_avoidance: role_support_redesign_candidate
R3_recovery_after_limit: role_support_redesign_candidate
R4_unavoidable_mitigation: role_support_redesign_candidate
R5_hidden_dynamics_robustness: role_support_redesign_candidate
```

The remaining R2-R5 labels do not become training targets yet. They indicate
that support coverage or role semantics still need audit before any comparison,
ranking, or paper-level claim.

## Claim Boundary

Allowed claim:

```text
M2315 completed a no-rerun metric semantics conflict diagnosis over M2313
support-policy artifacts.
```

Blocked claims:

```text
controller-family ranking;
checkpoint promotion;
driver performance improvement;
paper-level benchmark evidence;
finite-window vs GRU conclusion;
level3 self-identification evidence.
```

## Follow-Up

Pre-register and run a result audit:

```text
m2316-paper-route-current-sim-scenario-task-family-metric-semantics-conflict-diagnosis-result-audit
```

M2316 should decide whether the next route is a role-specific safe-stop success
semantics repair for R0, residual support-redesign for R2-R5, or a combined
success semantics plus support coverage audit. It must not run training,
rollout, ranking, or self-ID tests.
