# M1787 Role-Specific Panel/Metric Repair Materialization Preflight

- status: completed
- decision: `role_specific_panel_metric_repair_materialization_pass_route_to_result_audit`
- summary: `runs/m1787_role_specific_panel_metric_repair_materialization_preflight/summary.json`
- no reset: true
- no rollout: true
- training/replay/PPO: false

## Summary

M1787 materialized the M1786 v2 role-specific panel/metric repair contract into
no-rollout artifacts. It did not run reset, rollout, replay, PPO, or training.

Result:

```text
result_class: role_specific_panel_metric_repair_materialization_preflight_pass
role_surface_count: 6
profile_control_count: 12
metric_contract_rows: 33
admissibility_contract_rows: 6
panel_repair_matrix_rows: 276
metric_only_repair_plan_rows: 4
new_materialization_required_rows: 6
claim_boundary_rows: 7
ranking_admissible_by_default: false
mitigation_uses_obstacle_pass_success_as_primary: false
profile_controls_preserved: true
guardrail_violation_count: 0
```

Written artifacts:

```text
runs/m1787_role_specific_panel_metric_repair_materialization_preflight/summary.json
runs/m1787_role_specific_panel_metric_repair_materialization_preflight/role_surface_contract.csv
runs/m1787_role_specific_panel_metric_repair_materialization_preflight/metric_contract_v2.csv
runs/m1787_role_specific_panel_metric_repair_materialization_preflight/admissibility_contract.csv
runs/m1787_role_specific_panel_metric_repair_materialization_preflight/panel_repair_specs.json
runs/m1787_role_specific_panel_metric_repair_materialization_preflight/panel_repair_matrix.csv
runs/m1787_role_specific_panel_metric_repair_materialization_preflight/metric_only_repair_plan.csv
runs/m1787_role_specific_panel_metric_repair_materialization_preflight/new_materialization_required.csv
runs/m1787_role_specific_panel_metric_repair_materialization_preflight/claim_boundary.csv
```

## Role Surfaces

The v2 contract materializes six surfaces:

```text
stable_avoidance_aes:
  task_label: aeb_feasible|aes_feasible
  primary_metric: admissible_obstacle_pass_rate
  admissibility_gate: collision_rate_low_and_off_track_rate_low

drift_required_recovery:
  task_label: drift_required
  primary_metric: controlled_recovery_stage_pass_rate
  admissibility_gate: obstacle_clearance_and_post_maneuver_recovery_observed

hidden_robust_aes_feasible:
  task_label: aes_feasible
  primary_metric: worst_hidden_bucket_success_rate
  admissibility_gate: label_pure_hidden_bucket_balance

hidden_robust_drift_required:
  task_label: drift_required
  primary_metric: worst_hidden_bucket_controlled_recovery_rate
  admissibility_gate: label_pure_hidden_bucket_balance

hidden_robust_unavoidable_mitigation:
  task_label: unavoidable
  primary_metric: worst_hidden_bucket_impact_severity_proxy_mean
  admissibility_gate: label_pure_hidden_bucket_balance

unavoidable_mitigation:
  task_label: unavoidable
  primary_metric: impact_severity_proxy_mean
  admissibility_gate: mitigation_surface_only_no_avoidance_ranking
```

Every surface has:

```text
ranking_admissible_by_default: false
diagnostic_only_no_ranking_claim: true
requires_new_materialization: true
preserves_profile_controls: true
```

## Contract Checks

The preflight preserves the M1786 repair constraints:

- stable AES has an explicit collision/off-track admissibility gate;
- drift-required recovery has a staged controlled-recovery surface;
- hidden robustness is split by task label and hidden bucket family;
- unavoidable mitigation uses severity, not obstacle-pass success;
- profile controls from the M1783 scorecard are preserved;
- ranking remains blocked by default.

The claim boundary explicitly allows only v2 contract materialization and
disallows reset, rollout, controller-family ranking, profile promotion,
paper-level evidence, and level3 self-identification.

## Guardrails

- environment reset started: `false`
- environment rollout started: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- v2 role-specific panel/metric repair contract artifacts exist;
- ranking is blocked by default;
- the repaired contract is ready for result audit.

Unsupported:

- reset feasibility;
- measured execution;
- controller-family ranking;
- profile promotion;
- private-holdout evidence;
- paper-level benchmark evidence;
- level3 self-identification.

## Decision

Route to M1788 materialization result audit before any reset feasibility or
measured execution.
