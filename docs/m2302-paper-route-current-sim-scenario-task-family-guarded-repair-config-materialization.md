# M2302 Paper-Route Current-Sim Scenario Task-Family Guarded-Repair Config Materialization

- status: completed
- result_class: `current_sim_scenario_task_family_guarded_repair_config_materialization_pass`
- manifest: `experiments/manifests/m2302-paper-route-current-sim-scenario-task-family-guarded-repair-config-materialization.json`
- summary: `runs/m2302_paper_route_current_sim_scenario_task_family_guarded_repair_configs/summary.json`
- runner: `src/autodrift/paper_route_current_sim_scenario_task_family_guarded_repair_config_materialization.py`
- tests: `tests/test_paper_route_current_sim_scenario_task_family_guarded_repair_config_materialization.py`
- reset/rollout/policy action: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Command

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_scenario_task_family_guarded_repair_config_materialization \
  --source-config-root runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/configs \
  --repair-gate-spec runs/m2298_paper_route_current_sim_scenario_task_family_offtrack_primary_collision_guardrail/repair_gate_spec.json \
  --output-dir runs/m2302_paper_route_current_sim_scenario_task_family_guarded_repair_configs \
  --training-output-root runs/m2303_paper_route_current_sim_scenario_task_family_guarded_repair_training_execution \
  --next-blocker m2303-paper-route-current-sim-scenario-task-family-guarded-repair-training-execution-design
```

## Materialization Result

```text
config_count: 15
target_config_count: 15
profile_count: 5
seed_count: 3
budget_signature_count: 1
actor_contract_violation_count: 0
track_width_widened_count: 0
reward_changed_config_count: 15
profile_specific_tuning_count: 0
ranking_admissible_count: 0
winner_selected_count: 0
repair_gate_spec_copied: true
guardrail_violation_count: 0
```

M2302 carries forward the accepted M2298 gate pack:

```text
offtrack_target_slice_count: 20
collision_guardrail_slice_count: 11
```

## Guarded-V2 Reward Changes

M2302 changes the shared reward/config knobs for every profile and seed:

```text
track_cost_scale: 3.4
heading_cost_scale: 0.35
road_margin_cost_scale: 3.4
road_margin_warning_fraction: 0.45
off_track_penalty: 10.0
termination_penalty: 8.0
dense_clearance_margin_reward_scale: 0.5
dense_clearance_margin_reward_window: 10.0
clearance_margin_reward_scale: 1.0
clearance_margin_reward_clip: 0.25
collision_penalty: 25.0
```

These are shared knobs, not profile-specific tuning. The scenario specs,
track width, actor inputs, and profile definitions are unchanged.

## Artifacts

```text
runs/m2302_paper_route_current_sim_scenario_task_family_guarded_repair_configs/summary.json
runs/m2302_paper_route_current_sim_scenario_task_family_guarded_repair_configs/training_matrix.csv
runs/m2302_paper_route_current_sim_scenario_task_family_guarded_repair_configs/generated_config_paths.json
runs/m2302_paper_route_current_sim_scenario_task_family_guarded_repair_configs/repair_gate_spec.json
runs/m2302_paper_route_current_sim_scenario_task_family_guarded_repair_configs/claim_boundary.csv
runs/m2302_paper_route_current_sim_scenario_task_family_guarded_repair_configs/configs/
```

## Claim Boundary

M2302 is config materialization only. It does not show that the repair improves
behavior.

M2302 cannot claim:

- training completed;
- controller-family ranking;
- winner selection;
- paper-level benchmark result;
- finite-window vs GRU conclusion;
- level3 self-identification.

## Next

Pre-registered follow-up:

```text
m2303-paper-route-current-sim-scenario-task-family-guarded-repair-training-execution-design
```
