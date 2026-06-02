# M2458 Paper-Route Current-Sim Dual-Axis Scenario-Quality Redesign Reset/Static Preflight Adapter Implementation

- status: completed
- result_class: `scenario_quality_redesign_reset_static_preflight_adapter_static_pass_reset_blocked`
- manifest: `experiments/manifests/m2458-paper-route-current-sim-dual-axis-scenario-quality-redesign-reset-static-preflight-adapter-implementation.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_scenario_quality_redesign_reset_static_preflight_adapter.py`
- tests: `tests/test_paper_route_current_sim_dual_axis_scenario_quality_redesign_reset_static_preflight_adapter.py`
- summary: `runs/m2458_paper_route_current_sim_dual_axis_scenario_quality_redesign_reset_static_preflight_adapter/summary.json`
- preflight work items: `runs/m2458_paper_route_current_sim_dual_axis_scenario_quality_redesign_reset_static_preflight_adapter/preflight_work_items.csv`
- static checks: `runs/m2458_paper_route_current_sim_dual_axis_scenario_quality_redesign_reset_static_preflight_adapter/static_check_rows.csv`
- reset checks: `runs/m2458_paper_route_current_sim_dual_axis_scenario_quality_redesign_reset_static_preflight_adapter/reset_check_rows.csv`
- overlay requirements: `runs/m2458_paper_route_current_sim_dual_axis_scenario_quality_redesign_reset_static_preflight_adapter/overlay_requirement_rows.csv`
- guardrails: `runs/m2458_paper_route_current_sim_dual_axis_scenario_quality_redesign_reset_static_preflight_adapter/guardrail_rows.csv`
- claim boundary: `runs/m2458_paper_route_current_sim_dual_axis_scenario_quality_redesign_reset_static_preflight_adapter/claim_boundary.csv`
- decision rows: `runs/m2458_paper_route_current_sim_dual_axis_scenario_quality_redesign_reset_static_preflight_adapter/decision_rows.csv`
- reset/rollout/policy action/scenario-redesign execution/repair/training/replay/PPO: `false`
- ranking/winner selection: `false`
- actual-success improvement/paper/FW-vs-GRU/level3 self-ID/scenario-redesign-executed/training-repair/current-sim verdict claims: `false`

## Result

M2458 implemented and ran the reset/static preflight adapter from the M2457
design. It produced one work item for every M2455 candidate row and ran static
checks over all of them.

```text
source_candidate_row_count: 30
preflight_work_item_count: 30
static_check_row_count: 246
static_check_pass_count: 246
static_check_fail_count: 0
reset_required_count: 6
concrete_overlay_available_count: 0
reset_attempted_count: 0
reset_success_count: 0
reset_blocked_missing_concrete_overlay_count: 6
guardrail_violation_count: 0
```

Preflight lanes:

```text
reset_blocked: 6
static_only: 24
```

Candidate groups:

```text
stable_feasibility_support: 3
stable_aes_support: 3
geometry_timing_guardrail: 7
handling_limit_guardrail: 5
hidden_dynamics_guardrail: 9
mitigation_guardrail: 3
```

## Interpretation

The adapter confirms that M2455's protocol rows are static-valid, but not reset
ready. The six stable/AES support rows require concrete numeric environment
overlays before reset validation:

```text
obstacle.distance_range
obstacle.lateral_offset_range
obstacle.half_width_range
speed_range
```

Those overlays are absent in M2455, so the adapter correctly records:

```text
reset_blocked_missing_concrete_overlay_count: 6
```

This is a scenario-spec readiness blocker, not a driver performance result. It
does not say the policy can or cannot drive these tasks. It says the protocol
artifact does not yet contain enough numeric env configuration to instantiate
and reset those stable/AES scenarios safely.

## Guardrails

All claim and contract guardrails remain clean:

```text
labels_enter_actor_input_count: 0
actor_input_contract_changed_count: 0
policy_action_executed: false
scenario_redesign_executed: false
repair_execution_started: false
training_started: false
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
```

The adapter did not execute reset, rollout, policy inference, repair, training,
ranking, or winner selection.

## Decision

Accepted next route:

```text
m2459-paper-route-current-sim-dual-axis-scenario-quality-redesign-reset-static-preflight-adapter-result-audit
```

M2459 should audit the static-pass/reset-blocked evidence and choose between a
concrete overlay design route, branch synthesis, or stop. It must not execute
rollout, policy actions, scenario redesign, repair, training, ranking, winner
selection, or verdict claims.
