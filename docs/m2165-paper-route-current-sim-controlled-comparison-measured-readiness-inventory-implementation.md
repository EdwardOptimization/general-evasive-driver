# M2165 Paper-Route Current-Sim Controlled-Comparison Measured Readiness Inventory Implementation

- status: completed
- decision: `current_sim_measured_readiness_inventory_complete_route_to_result_audit`
- parent design: `docs/m2164-paper-route-current-sim-controlled-comparison-measured-execution-command-design.md`
- implementation: `src/autodrift/paper_route_current_sim_controlled_comparison_measured_readiness_inventory.py`
- tests: `tests/test_paper_route_current_sim_controlled_comparison_measured_readiness_inventory.py`
- summary: `runs/m2165_paper_route_current_sim_controlled_comparison_measured_readiness_inventory/summary.json`
- environment reset started: `false`
- environment rollout started: `false`
- policy action executed: `false`
- measured execution started: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

M2165 ran the frozen no-rollout readiness inventory:

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_controlled_comparison_measured_readiness_inventory \
  --executable-task-specs runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/executable_task_specs.json \
  --workload runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/planned_workload.csv \
  --output-dir runs/m2165_paper_route_current_sim_controlled_comparison_measured_readiness_inventory \
  --target-spec-count 40 \
  --target-workload-count 320 \
  --target-profile-count 8 \
  --next-blocker m2166-paper-route-current-sim-measured-readiness-inventory-result-audit
```

Focused tests:

```text
tests/test_paper_route_current_sim_controlled_comparison_measured_readiness_inventory.py: 1 passed
```

## Result

The inventory completes and confirms that the panel is not measured-ready yet.

```text
result_class: current_sim_measured_readiness_inventory_complete
input_executable_spec_count: 40
input_workload_count: 320
profile_count: 8
count_pass: true
checkpoint_required_workload_count: 320
checkpoint_path_missing_count: 320
checkpoint_path_present_count: 0
checkpoint_path_exists_count: 0
workload_ready_count: 0
profile_ready_count: 0
old_runner_name: paper_route_controlled_routing_smoke_measured_runner
old_runner_required_field_count: 20
old_runner_missing_field_count: 12
old_runner_compatible_with_current_sim_panel: false
guardrail_violation_count: 0
environment_rollout_started: false
policy_action_executed: false
measured_rollout_started: false
training_started: false
replay_started: false
ppo_used: false
controller_family_ranking_claim_made: false
winner_selected: false
finite_window_vs_gru_conclusion_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

Per-profile readiness:

```text
L0_current_masked: 40/40 checkpoint paths missing, ready false
L1_one_step:       40/40 checkpoint paths missing, ready false
L2_window_13:      40/40 checkpoint paths missing, ready false
L2_window_25:      40/40 checkpoint paths missing, ready false
L2_window_50:      40/40 checkpoint paths missing, ready false
L2_window_100:     40/40 checkpoint paths missing, ready false
L3_online_gru:     40/40 checkpoint paths missing, ready false
L3_reset_control:  40/40 checkpoint paths missing, ready false
```

Old-runner missing fields:

```text
panel_source_id
panel_task_family
source_origin
source_edge
window_tag
source_role_semantics
parent_feasibility_tier_id
normalized_surface_variant
sampled_obstacle_label
proxy_template_family
generated_source_row
paper_validity_claim
```

## Artifacts

```text
runs/m2165_paper_route_current_sim_controlled_comparison_measured_readiness_inventory/summary.json
runs/m2165_paper_route_current_sim_controlled_comparison_measured_readiness_inventory/workload_readiness_rows.csv
runs/m2165_paper_route_current_sim_controlled_comparison_measured_readiness_inventory/profile_readiness_rows.csv
runs/m2165_paper_route_current_sim_controlled_comparison_measured_readiness_inventory/runner_schema_gap_rows.csv
runs/m2165_paper_route_current_sim_controlled_comparison_measured_readiness_inventory/claim_boundary.csv
runs/m2165_paper_route_current_sim_controlled_comparison_measured_readiness_inventory/run_state.json
```

## Supported Claims

M2165 supports:

- the reset-valid M2151 panel is not measured-ready yet;
- checkpoint materialization or training is required for all 8 profile families;
- old measured runners are not schema-compatible with the current-sim panel;
- a current-sim-specific runner or adapter is required.

M2165 does not support:

- measured execution;
- controller-family ranking or winner selection;
- paper-level benchmark evidence;
- finite-window vs GRU verdicts;
- level3 self-identification.

## Next

Next milestone:

```text
m2166-paper-route-current-sim-measured-readiness-inventory-result-audit
```

M2166 should audit the readiness blockers and decide the next repair order:
checkpoint/profile materialization, current-sim runner implementation, or both
as a staged route.
