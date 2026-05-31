# M2047 Paper-Route Controlled Routing Smoke Task-Quality Repair Source Mining Design

- status: completed
- decision: `controlled_routing_smoke_task_quality_repair_source_mining_design_admit_materialization_preflight_implementation`
- manifest: `experiments/manifests/m2047-paper-route-controlled-routing-smoke-task-quality-repair-source-mining-design.json`
- reset/rollout/measured execution in M2047: `false`
- policy actions executed in M2047: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2045 creates 192 repair templates. They are not executable task specs. M2047
designs the deterministic no-reset conversion into concrete repaired task specs
and planned workload rows.

The implementation should write:

```text
runs/m2048_paper_route_controlled_routing_smoke_task_quality_repair_materialization_preflight/summary.json
runs/m2048_paper_route_controlled_routing_smoke_task_quality_repair_materialization_preflight/executable_task_specs.json
runs/m2048_paper_route_controlled_routing_smoke_task_quality_repair_materialization_preflight/executable_task_specs.csv
runs/m2048_paper_route_controlled_routing_smoke_task_quality_repair_materialization_preflight/planned_workload.csv
runs/m2048_paper_route_controlled_routing_smoke_task_quality_repair_materialization_preflight/claim_boundary.csv
```

No reset, rollout, measured execution, ranking, or training occurs in this
step.

## Parent Resolution

The implementation must resolve each repair template to a concrete parent spec
from:

```text
runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/executable_task_specs.json
```

Resolution order:

```text
1. exact task_source_id:
   use parent_task_source_id if it matches an M2033 executable spec.

2. source-profile slice:
   for L2 profile-only templates, use
   runs/m2042.../outcome_by_source_profile.csv and choose rows matching
   parent_profile_name with offtrack outcome; then resolve task_source_id.

3. family slice:
   for family_offtrack_relief, cycle through M2033 specs matching
   parent_panel_task_family.

4. source-kind slice:
   for zero_success_source_kind_relief, cycle through M2033 specs matching
   parent_source_kind.

5. generated proxy slice:
   for generated_proxy_support_check, cycle through M2033 specs with
   generated_source_row=true and materialization_semantics=smoke_proxy.
```

Fail closed if no parent spec can be resolved. Do not synthesize an executable
spec without a concrete parent.

## Delta Application

Clone the resolved parent spec and apply only task-quality deltas from the
template:

```text
env_config.obstacle.distance_range += obstacle_distance_delta_m
env_config.obstacle.half_width_range += obstacle_half_width_delta_m
env_config.track_width += track_width_delta_m
env_config.warmup_gate.reveal_step += warmup_reveal_step_delta
env_config.max_steps += max_steps_delta
```

Bounds:

```text
obstacle distance min >= 8.0
obstacle half-width min >= 0.25
track_width >= 4.0
warmup reveal_step >= 0
max_steps >= parent max_steps
```

Do not change:

```text
actor observation contract;
controller profile configs;
checkpoint paths;
history_length;
wheel_observation_mode;
include_privileged_params;
obstacle_relative_velocity_mode;
paper_validity_claim.
```

## Output Metadata

Each repaired spec should preserve or add:

```text
task_source_id = m2048-repair-{repair_candidate_id}
panel_source_id = parent panel_source_id
panel_task_family = parent panel_task_family
source_kind = parent source_kind
repair_axis = template repair_axis
repair_candidate_id
repair_branch_id
repair_source_family
parent_task_source_id
parent_resolution_method
parent_resolution_key
generated_source_row = template target_generated_source_row
materialization_semantics = smoke_proxy
paper_validity_claim = false
profile_specific_tuning = false
controller_family_ranking_claim_made = false
finite_window_vs_gru_conclusion_made = false
paper_level_claim_made = false
level3_self_id_claim_made = false
```

Planned workload:

```text
192 repaired specs x 12 existing controller profiles = 2304 workload rows
```

The implementation may reuse M2033 profile metadata, but must not alter any
profile config or checkpoint.

## Guardrails

The materialization preflight passes only if:

```text
repaired_spec_count = 192
planned_workload_count = 2304
repair-axis quotas match 64/48/40/24/16
source split counts match 112/80
unresolved_parent_count = 0
contract_violation_count = 0
forbidden_claim_count = 0
generated_proxy_paper_claim_count = 0
profile_specific_tuning_count = 0
environment_reset_started = false
environment_rollout_started = false
policy_action_executed = false
measured_rollout_started = false
```

## Next

M2048 should implement this no-reset materialization preflight with focused
tests. Reset validation, measured execution, ranking, finite-window-vs-GRU,
paper-level comparison, and level3 self-ID claims remain blocked.
