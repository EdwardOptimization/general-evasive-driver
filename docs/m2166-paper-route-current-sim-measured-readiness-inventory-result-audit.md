# M2166 Paper-Route Current-Sim Measured Readiness Inventory Result Audit

- status: completed
- decision: `current_sim_readiness_inventory_audit_route_to_runner_adapter_design_first`
- audited artifact: `runs/m2165_paper_route_current_sim_controlled_comparison_measured_readiness_inventory/summary.json`
- inventory rerun in M2166: `false`
- rollout/measured execution in M2166: `false`
- policy actions executed in M2166: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Audit Result

M2166 audits M2165 as a clean no-rollout readiness inventory with two concrete
measured-readiness blockers.

```text
result_class: current_sim_measured_readiness_inventory_complete
input_executable_spec_count: 40
input_workload_count: 320
profile_count: 8
checkpoint_required_workload_count: 320
checkpoint_path_missing_count: 320
checkpoint_path_present_count: 0
checkpoint_path_exists_count: 0
workload_ready_count: 0
profile_ready_count: 0
old_runner_missing_field_count: 12
old_runner_compatible_with_current_sim_panel: false
guardrail_violation_count: 0
environment_rollout_started: false
policy_action_executed: false
measured_rollout_started: false
training_started: false
replay_started: false
ppo_used: false
```

## Blocker Classification

### Blocker A: missing checkpoint materialization

Every workload row requires a checkpoint for measured execution:

```text
checkpoint_required_workload_count: 320
checkpoint_path_missing_count: 320
```

This blocks real measured rollout. It does not invalidate the reset-valid
scenario panel; it means the controller-family comparison is still at the
profile/checkpoint materialization stage.

### Blocker B: old measured-runner schema mismatch

The old controlled-routing measured runner misses 12 required fields on the
current-sim panel:

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

This blocks direct runner reuse. It is a schema lineage issue, not a driver
behavior issue.

## Repair Order

M2166 chooses a staged repair, with runner compatibility first:

```text
1. Design a current-sim-specific measured runner adapter.
2. Implement the adapter with focused fake-rollout tests and strict no-overclaim
   claim boundary.
3. Audit runner compatibility.
4. Design checkpoint/profile materialization or training for the 8 profile
   families.
5. Only after checkpoints and runner compatibility are both clean, freeze a real
   320-episode measured-execution command.
```

Reason:

```text
Checkpoint training/materialization will be expensive and should target the
final measured-runner schema. Building the adapter first removes schema
uncertainty and gives checkpoint repair a concrete output contract.
```

## Claim Boundary

Supported:

- current-sim measured execution is blocked by checkpoint readiness and runner
  schema readiness;
- both blockers are explicit and auditable;
- current-sim-specific measured runner design is the next repair step.

Unsupported:

- measured execution;
- controller-family ranking or winner selection;
- paper-level benchmark evidence;
- finite-window vs GRU verdicts;
- level3 self-identification.

## Next

Next milestone:

```text
m2167-paper-route-current-sim-measured-runner-adapter-design
```

M2167 must design the current-sim measured runner adapter. It must not run
measured execution or train checkpoints.
