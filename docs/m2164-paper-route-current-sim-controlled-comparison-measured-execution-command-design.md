# M2164 Paper-Route Current-Sim Controlled-Comparison Measured Execution Command Design

- status: completed
- decision: `current_sim_measured_execution_command_design_blocked_by_checkpoint_and_runner_readiness_inventory`
- parent synthesis: `docs/m2163-paper-route-current-sim-controlled-comparison-post-reset-branch-synthesis.md`
- reset rerun in M2164: `false`
- rollout/measured execution in M2164: `false`
- policy actions executed in M2164: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Compatibility Check

M2164 does not freeze a real measured-execution command yet. Two readiness
blockers must be made explicit first.

### Existing runner schema mismatch

The old controlled-routing smoke runner expects metadata such as:

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

The M2151 current-sim workload instead carries:

```text
benchmark_spec_id
profile_level
checkpoint_required_for_measured_execution
task_family
history_representation
history_window_steps
reset_or_truncated_control
environment_reset_scheduled
environment_rollout_scheduled
finite_window_vs_gru_conclusion_made
```

Therefore using an old runner directly would either fail validation or erase
the current-sim comparison semantics. A current-sim-specific measured runner or
adapter is required.

### Checkpoint readiness gap

M2151 deliberately left measured-execution checkpoint paths empty:

```text
checkpoint_path: ""
checkpoint_required_for_measured_execution: true
```

This is acceptable for reset validation, but not for measured execution. The
next step must inventory the profile/checkpoint readiness state before any
rollout command is frozen.

## Frozen Readiness Inventory Command

M2165 should implement and run only a no-rollout readiness inventory:

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

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_paper_route_current_sim_controlled_comparison_measured_readiness_inventory.py
```

## Planned M2165 Artifacts

```text
runs/m2165_paper_route_current_sim_controlled_comparison_measured_readiness_inventory/summary.json
runs/m2165_paper_route_current_sim_controlled_comparison_measured_readiness_inventory/workload_readiness_rows.csv
runs/m2165_paper_route_current_sim_controlled_comparison_measured_readiness_inventory/profile_readiness_rows.csv
runs/m2165_paper_route_current_sim_controlled_comparison_measured_readiness_inventory/runner_schema_gap_rows.csv
runs/m2165_paper_route_current_sim_controlled_comparison_measured_readiness_inventory/claim_boundary.csv
runs/m2165_paper_route_current_sim_controlled_comparison_measured_readiness_inventory/run_state.json
```

## Pass Gates

M2165 passes if the no-rollout inventory completes and exposes readiness
blockers without running policy behavior:

```text
result_class == current_sim_measured_readiness_inventory_complete
input_executable_spec_count == 40
input_workload_count == 320
profile_count == 8
environment_rollout_started == false
policy_action_executed == false
measured_rollout_started == false
training_started == false
replay_started == false
ppo_used == false
controller_family_ranking_claim_made == false
finite_window_vs_gru_conclusion_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
guardrail_violation_count == 0
```

The expected readiness result is not full readiness. It is expected to report
the current checkpoint gap and old-runner schema mismatch explicitly.

## Claim Boundary

Supported:

```text
the measured-execution command cannot be frozen until checkpoint paths and
current-sim runner schema compatibility are repaired.
```

Unsupported:

```text
measured driver performance;
controller-family ranking;
winner selection;
finite-window vs GRU verdict;
paper-level benchmark evidence;
level3 self-identification.
```

## Next

Next milestone:

```text
m2165-paper-route-current-sim-controlled-comparison-measured-readiness-inventory-implementation
```
