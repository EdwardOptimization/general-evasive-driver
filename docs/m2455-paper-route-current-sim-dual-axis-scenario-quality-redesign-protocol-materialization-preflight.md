# M2455 Paper-Route Current-Sim Dual-Axis Scenario-Quality Redesign Protocol Materialization Preflight

- status: completed
- result_class: `current_sim_dual_axis_scenario_quality_redesign_protocol_materialization_preflight_pass`
- manifest: `experiments/manifests/m2455-paper-route-current-sim-dual-axis-scenario-quality-redesign-protocol-materialization-preflight.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_scenario_quality_redesign_protocol_materialization_preflight.py`
- tests: `tests/test_paper_route_current_sim_dual_axis_scenario_quality_redesign_protocol_materialization_preflight.py`
- summary: `runs/m2455_paper_route_current_sim_dual_axis_scenario_quality_redesign_protocol_materialization_preflight/summary.json`
- candidate rows: `runs/m2455_paper_route_current_sim_dual_axis_scenario_quality_redesign_protocol_materialization_preflight/candidate_rows.csv`
- role protocol rows: `runs/m2455_paper_route_current_sim_dual_axis_scenario_quality_redesign_protocol_materialization_preflight/role_protocol_rows.csv`
- geometry lever rows: `runs/m2455_paper_route_current_sim_dual_axis_scenario_quality_redesign_protocol_materialization_preflight/geometry_lever_rows.csv`
- guardrail rows: `runs/m2455_paper_route_current_sim_dual_axis_scenario_quality_redesign_protocol_materialization_preflight/guardrail_rows.csv`
- claim boundary: `runs/m2455_paper_route_current_sim_dual_axis_scenario_quality_redesign_protocol_materialization_preflight/claim_boundary.csv`
- decision rows: `runs/m2455_paper_route_current_sim_dual_axis_scenario_quality_redesign_protocol_materialization_preflight/decision_rows.csv`
- rollout/policy action/scenario-redesign execution/repair/training/replay/PPO: `false`
- ranking/winner selection: `false`
- actual-success improvement/paper/FW-vs-GRU/level3 self-ID/scenario-redesign-executed/training-repair/current-sim verdict claims: `false`

## Result

M2455 materialized M2454's protocol into non-ranking artifact tables.

```text
source_panel_row_count: 71
candidate_row_count: 30
role_protocol_row_count: 5
geometry_lever_row_count: 6
guardrail_row_count: 15
claim_boundary_row_count: 8
decision_row_count: 4
guardrail_violation_count: 0
```

Candidate group counts:

```text
stable_feasibility_support: 3
stable_aes_support: 3
geometry_timing_guardrail: 7
handling_limit_guardrail: 5
hidden_dynamics_guardrail: 9
mitigation_guardrail: 3
```

Split counts:

```text
public_debug: 23
public_gate: 7
```

## Protocol Groups

M2455 materialized the required role groups:

```text
stable_feasibility_support:
  R0/aeb_feasible rows for stable road-contained obstacle-avoidance support.

stable_aes_support:
  R1/aes_feasible rows for AEB-infeasible but stable steering-avoidance support.

handling_limit_guardrail:
  R2/R3/R5 and drift_required rows preserved as guardrails and later repair-plan candidates.

hidden_dynamics_guardrail:
  hidden-dynamics bucket rows preserved as metadata-only stress guardrails.

mitigation_guardrail:
  R4/unavoidable rows isolated from success ranking.
```

The materialized candidates remain protocol rows only. They are not executed
scenario changes and they do not claim success readiness.

## Guardrails

All claim-boundary and contract guardrails pass:

```text
labels_enter_actor_input_count: 0
actor_input_contract_changed_count: 0
scenario_redesign_executed: false
policy_action_executed: false
repair_execution_started: false
training_started: false
ranking_admissible_count: 0
winner_selected_count: 0
```

The claim boundary explicitly blocks:

```text
actual_success_improvement
paper_or_self_id_verdict
current_sim_verdict
scenario_redesign_executed
measured_rollout_started
repair_training_started
ranking_or_winner
```

## Supported Claims

Supported:

```text
M2454's scenario-quality protocol can be materialized into deterministic,
non-ranking candidate, role, geometry, guardrail, claim-boundary, and decision
artifacts.

Stable-feasibility, stable-AES, handling-limit, hidden-dynamics, and mitigation
guardrail groups are all nonempty.

The materialized artifacts preserve the actor-input contract and do not execute
redesign, rollout, repair, training, ranking, or winner selection.
```

## Rejected Claims

Still blocked:

```text
scenario redesign was executed
driver performance improved
actual success improved
repair/training readiness
controller/profile/pack/checkpoint ranking
candidate-family ranking
winner selection
paper-level result
finite-window-vs-GRU result
level3 self-identification
current-sim verdict
```

## Decision

Next milestone:

```text
m2456-paper-route-current-sim-dual-axis-scenario-quality-redesign-protocol-materialization-result-audit
```

M2456 should audit the materialized artifacts before reset/static preflight,
measured rollout, scenario redesign execution, repair-plan design, training, or
verdict claims.
