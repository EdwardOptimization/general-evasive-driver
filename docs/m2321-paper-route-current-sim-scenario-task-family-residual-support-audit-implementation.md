# M2321 Paper-Route Current-Sim Scenario Task-Family Residual Support Audit Implementation

- status: completed
- result_class: `current_sim_scenario_task_family_residual_support_audit_pass`
- manifest: `experiments/manifests/m2321-paper-route-current-sim-scenario-task-family-residual-support-audit-implementation.json`
- design doc: `docs/m2320-paper-route-current-sim-scenario-task-family-residual-support-audit-design.md`
- summary: `runs/m2321_paper_route_current_sim_scenario_task_family_residual_support_audit/summary.json`
- runner: `src/autodrift/paper_route_current_sim_scenario_task_family_residual_support_audit.py`
- focused tests: `tests/test_paper_route_current_sim_scenario_task_family_residual_support_audit.py`
- reset/rollout/policy action in M2321: `false`
- training/replay/PPO in M2321: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Command

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_scenario_task_family_residual_support_audit \
  --episode-rows runs/m2318_paper_route_current_sim_scenario_task_family_role_success_semantics_repair/episode_rows_rescored.csv \
  --scenario-support-labels runs/m2318_paper_route_current_sim_scenario_task_family_role_success_semantics_repair/scenario_support_labels_rescored.csv \
  --role-support-summary runs/m2318_paper_route_current_sim_scenario_task_family_role_success_semantics_repair/role_support_summary_rescored.csv \
  --output-dir runs/m2321_paper_route_current_sim_scenario_task_family_residual_support_audit \
  --target-scenario-count 72 \
  --target-residual-scenario-count 48 \
  --next-blocker m2322-paper-route-current-sim-scenario-task-family-residual-support-audit-result-audit
```

## Artifact Completeness

M2321 is artifact-only and complete:

```text
input_episode_count: 1080
input_scenario_count: 72
input_role_summary_count: 6
residual_scenario_count: 48
guardrail_violation_count: 0
```

Written artifacts:

```text
summary.json
residual_scenario_rows.csv
residual_role_summary.csv
residual_axis_summary.csv
residual_route_summary.csv
residual_support_policy_summary.csv
claim_boundary.csv
run_state.json
```

## Residual Counts

Support labels:

```text
support_clear: 24
support_mixed: 26
support_blocked: 21
metric_conflict: 1
```

Residual support labels:

```text
support_mixed: 26
support_blocked: 21
metric_conflict: 1
```

Role residual counts:

```text
R0_stable_avoidable: 0
R1_aeb_infeasible_stable_aes: 0
R2_handling_limit_drift_capable_avoidance: 12
R3_recovery_after_limit: 12
R4_unavoidable_mitigation: 12
R5_hidden_dynamics_robustness: 12
```

## Route Labels

M2321 classifies the 48 residual scenarios as:

```text
support_policy_coverage_candidate: 23
scenario_or_support_redesign_candidate: 12
mitigation_semantics_or_support_redesign_candidate: 12
metric_semantics_audit_candidate: 1
```

Role detail:

```text
R2:
  support_policy_coverage_candidate: 7
  scenario_or_support_redesign_candidate: 5

R3:
  support_policy_coverage_candidate: 8
  scenario_or_support_redesign_candidate: 3
  metric_semantics_audit_candidate: 1

R4:
  mitigation_semantics_or_support_redesign_candidate: 12

R5:
  support_policy_coverage_candidate: 8
  scenario_or_support_redesign_candidate: 4
```

Interpretation: R2/R3/R5 need coverage-vs-redesign separation; R4 should not be
treated as ordinary avoidance failure because unavoidable mitigation likely
needs a role-specific mitigation metric or support redesign.

## Claim Boundary

Allowed claim:

```text
M2321 completed an artifact-only residual-support classification over M2318
repaired artifacts.
```

Blocked claims:

```text
residual support solved;
driver performance result;
training result;
controller-family or support-policy ranking;
winner selection;
paper-level current-sim evidence;
finite-window vs GRU conclusion;
level3 self-identification evidence.
```

## Follow-Up

Pre-register result audit:

```text
experiments/manifests/m2322-paper-route-current-sim-scenario-task-family-residual-support-audit-result-audit.json
```
