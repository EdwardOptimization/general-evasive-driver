# M1788 Role-Specific Panel/Metric Repair Materialization Result Audit

- status: completed
- decision: `materialization_audit_admit_executable_panel_spec_design_before_reset`
- audited summary: `runs/m1787_role_specific_panel_metric_repair_materialization_preflight/summary.json`
- no reset in audit: true
- no rollout in audit: true
- training/replay/PPO: false

## Summary

M1788 audits the M1787 v2 role-specific panel/metric repair materialization. The
contract materialization is complete and coherent, but it is not yet an
executable reset-feasibility panel. M1787 writes role surfaces, metric
contracts, admissibility gates, and a profile/hidden-bucket matrix. It does not
yet write concrete reset-ready scenario specifications with seeds, road,
obstacle, hidden-dynamics, and sampler fields.

Therefore, M1788 does not admit reset feasibility yet. It routes to executable
v2 panel spec design.

Observed M1787 state:

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

## Contract Audit

M1787 satisfies the contract-level requirements:

- six role surfaces exist;
- stable AES has explicit collision/off-track admissibility;
- drift-required recovery has staged controlled-recovery semantics;
- hidden robustness is split into label-specific surfaces;
- unavoidable mitigation uses severity, not obstacle-pass success;
- all surfaces preserve profile controls;
- ranking is blocked by default;
- the claim boundary disallows reset, rollout, controller-family ranking,
  profile promotion, paper-level evidence, and level3 self-ID claims.

The required artifacts exist:

```text
summary.json
role_surface_contract.csv
metric_contract_v2.csv
admissibility_contract.csv
panel_repair_specs.json
panel_repair_matrix.csv
metric_only_repair_plan.csv
new_materialization_required.csv
claim_boundary.csv
```

## Reset-Readiness Audit

The materialization is not yet reset-ready. `panel_repair_matrix.csv` records:

```text
role_surface_id
profile_name
task_label
hidden_bucket_family
primary_metric
ranking_admissible_by_default
diagnostic_only_no_ranking_claim
preserves_profile_controls
```

That is enough for a contract audit, but not enough for reset feasibility. A
reset-ready panel must also contain executable scenario fields such as:

```text
scenario_id
eval_seed
role_surface_id
task_label
profile_name
road_bucket
obstacle_timing_bucket
obstacle_lateral_bucket
hidden_bucket_family
hidden_parameter_family
sampler_config
env_config_delta
expected_label_balance
```

Without these fields, reset feasibility would either be ambiguous or would need
to infer missing scenario semantics from earlier panels. That would violate the
manifest discipline.

## Route Decision

Route to M1789 executable v2 panel spec design before reset feasibility.

M1789 should:

- use M1787 contract artifacts and M1786 design;
- define reset-ready spec fields and balancing rules;
- state which M1770/M1777 bounded-panel fields can be reused;
- preserve the six v2 role surfaces and twelve profile controls;
- keep ranking blocked by default;
- not run reset or rollout.

Only after executable specs are materialized should a reset-only feasibility
preflight be admitted.

## Guardrails

- environment reset started in audit: `false`
- environment rollout started in audit: `false`
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

- M1787 v2 contract materialization is complete;
- M1787 is not yet reset-ready;
- executable panel spec design is required before reset feasibility.

Unsupported:

- reset feasibility;
- measured execution;
- controller-family ranking;
- profile promotion;
- private-holdout evidence;
- paper-level benchmark evidence;
- level3 self-identification.
