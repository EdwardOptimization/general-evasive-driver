# M2275 Paper-Route Current-Sim Scenario/Task-Quality Support Audit Result Audit

- status: completed
- decision: `current_sim_scenario_task_quality_support_audit_route_to_generation_design`
- manifest: `experiments/manifests/m2275-paper-route-current-sim-scenario-task-quality-support-audit-result-audit.json`
- parent result: `runs/m2274_paper_route_current_sim_scenario_task_quality_support_audit/summary.json`

## Audit Result

M2274 is complete and guardrail clean:

```text
result_class: current_sim_scenario_task_quality_support_audit_pass
episode_row_count: 1440
training_matrix_row_count: 60
missing_input_count: 0
guardrail_violation_count: 0
ranking_admissible_count: 0
winner_selected: false
primary_route: scenario_task_family_generation_design
```

The training matrices preserve the actor contract:

```text
hidden_oracle_actor_input_rows: 0
wheel_or_slip_actor_input_rows: 0
reference_or_ttc_actor_input_rows: 0
```

No reset, rollout, policy action, measured execution, training, replay, PPO,
private holdout, promotion, ranking, paper-level result, finite-window-vs-GRU
conclusion, or level3 self-identification claim was made.

## Support Gaps

The audit found good metric coverage:

```text
primary_metric_coverage: 10/10
```

But role and scenario support are incomplete:

```text
explicit_role_family_count: 3/6
role_family_label_completeness: 3/6
role_family_min_public_rows_64: 3/6
scenario_axis_direct_support: 8/11
```

Concrete gaps:

```text
R1_aeb_infeasible_stable_aes: missing
R3_recovery_after_limit: proxy only, no explicit role label
R5_hidden_dynamics_robustness: proxy only, no explicit role label
obstacle_longitudinal_timing_bucket: missing
obstacle_lateral_offset_bucket: missing
recovery_window_bucket: partial
```

This means the existing artifacts are useful diagnostic support but are not yet
a paper-grade role-specific current-sim benchmark pack.

## Decision

Accept M2274's route:

```text
scenario_task_family_generation_design
```

The next step should design explicit scenario/task-family generation and
metadata instrumentation. It should not start rollout/training yet.

M2276 should freeze:

```text
explicit role families and target support counts
scenario metadata schema
obstacle timing and lateral offset instrumentation
recovery-window instrumentation
hidden-dynamics robustness role labeling
artifact outputs for generated scenario configs
public/private holdout policy for later use
acceptance criteria before training
```

## Blocked Routes

Blocked:

```text
new rollout before scenario-family design
training before generated task support is materialized and audited
controller-family ranking
winner selection
finite-window-vs-GRU verdict
paper-level result
level3 self-identification
high-fidelity validation as primary route
```

## Next

Pre-register:

```text
m2276-paper-route-current-sim-scenario-task-family-generation-design
```
