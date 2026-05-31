# M2032 Paper-Route Controlled Routing Smoke Materialization Adapter Design

- status: completed
- decision: `controlled_routing_smoke_materialization_adapter_design_admit_no_reset_preflight_implementation`
- blocker source: `docs/m2031-paper-route-controlled-routing-smoke-command-design.md`
- source panel: `runs/m2029_paper_route_t2_t3_source_generation_preflight/merged_panel_sources.csv`
- generated specs: `runs/m2029_paper_route_t2_t3_source_generation_preflight/generated_source_specs.csv`
- reset/rollout/measured execution in M2032: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Purpose

M2032 designs the missing bridge between the M2029 coverage-ready source panel
and an executable routing-smoke workload. The adapter must be no-reset and
no-rollout. It should only materialize artifacts:

```text
selected smoke sources
executable task specs
planned workload rows
profile artifacts
metadata/coverage checks
claim boundary
summary
```

The adapter is not a benchmark and not a controller comparison. It only prepares
a bounded executable workload for a later reset/smoke route.

## Scope

Use a source-kind-balanced smoke subset rather than the full 237-source panel.

Selection rule:

```text
for each panel_task_family:
  select one deterministic representative source per source_kind
```

Expected selected source count from M2029 projection:

```text
T1 source kinds: 4
T2 source kinds: 10
T3 source kinds: 10
T4 source kinds: 4
T5 source kinds: 8
total selected smoke sources: 36
```

Profile scope:

```text
all 12 registered controller profiles
```

Planned workload size:

```text
36 selected sources x 12 profiles = 432 rows
```

This is large enough to validate profile routing and source-family coverage,
but small enough to remain a routing smoke rather than a full paper benchmark.

## Executable Semantics

The adapter must distinguish real executable provenance from smoke proxy
semantics.

### Existing lineage rows

Rows from historical source artifacts should preserve their source provenance:

```text
panel_source_id
panel_task_family
source_origin
source_kind
source_edge
window_tag
source_role_semantics
parent_feasibility_tier_id
normalized_surface_variant
sampled_obstacle_label
source_reference
```

Where a direct executable env config can be recovered from older artifacts, the
adapter should preserve that route. If it cannot, it should use a smoke proxy
and mark:

```text
materialization_semantics = smoke_proxy
paper_validity_claim = false
```

### M2029 generated T2/T3 rows

M2029 generated T2/T3 source rows are source-diversity artifacts, not validated
simulator tasks. For routing smoke, they may be materialized through deterministic
smoke proxy configs anchored to existing deployable human-view task templates.

Required labels:

```text
materialization_semantics = smoke_proxy
generated_source_row = true
paper_validity_claim = false
```

Allowed proxy template families:

```text
t4_actuator_delay_response
t4_staged_warmup_capability
t5_near_boundary_warmup
t5_boundary_axis_retarget
```

Mapping policy:

```text
brake_authority / drive_brake_asymmetry:
  use t4_staged_warmup_capability proxy

yaw_authority / steer_lag / rear_lateral_authority:
  use t4_actuator_delay_response proxy

mixed_authority:
  use t5_near_boundary_warmup proxy

terminal_boundary_recovery:
  use t5_boundary_axis_retarget proxy
```

This proxy mapping is acceptable only for routing-smoke plumbing. It must not be
used as paper-level T2/T3 task validity evidence.

## Output Schema

M2033 should implement a no-reset preflight and write:

```text
runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/summary.json
runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/selected_smoke_sources.csv
runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/executable_task_specs.json
runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/executable_task_specs.csv
runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/planned_workload.csv
runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/profile_artifacts.csv
runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/materialization_failures.csv
runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/source_kind_aggregate.csv
runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/family_source_kind_aggregate.csv
runs/m2033_paper_route_controlled_routing_smoke_materialization_preflight/claim_boundary.csv
```

### Executable task spec fields

Required top-level fields:

```text
task_source_id
panel_source_id
panel_task_family
source_origin
source_kind
source_edge
window_tag
source_role_semantics
parent_feasibility_tier_id
normalized_surface_variant
sampled_obstacle_label
source_reference
materialization_semantics
proxy_template_family
generated_source_row
paper_validity_claim
contract_checks
contract_violation_count
env_config
```

### Planned workload fields

Each selected executable source should be crossed with all 12 profiles:

```text
workload_id
task_source_id
panel_source_id
panel_task_family
profile_name
profile_config_path
checkpoint_path
source_origin
source_kind
source_edge
window_tag
source_role_semantics
parent_feasibility_tier_id
normalized_surface_variant
sampled_obstacle_label
materialization_semantics
proxy_template_family
generated_source_row
paper_validity_claim
environment_rollout_scheduled
training_scheduled
profile_specific_tuning
controller_family_ranking_claim_made
paper_level_claim_made
level3_self_id_claim_made
```

## Contract Checks

Every `env_config` must satisfy the deployable contract:

```text
include_privileged_params == false
wheel_observation_mode == none
action_history_mode == full
obstacle_relative_velocity_mode == zero
history_length >= 1
```

The adapter must also fail closed on:

```text
missing profile config/checkpoint
duplicate task_source_id
duplicate workload_id
missing selected family/source-kind representative
contract violation
generated-source row without materialization_semantics=smoke_proxy
paper_validity_claim=true for any smoke proxy row
```

## Result Classes

Expected result classes:

```text
controlled_routing_smoke_materialization_preflight_pass:
  selected source count = 36
  profile count = 12
  planned workload count = 432
  materialization failures = 0
  contract violations = 0
  guardrail violations = 0

controlled_routing_smoke_materialization_preflight_partial:
  artifacts are written, but some source kinds or profile artifacts are missing.

controlled_routing_smoke_materialization_preflight_fail_closed:
  executable semantics, provenance, profile artifacts, or contract checks fail.
```

Partial or fail-closed results must route to audit, not execution.

## Claim Boundary

M2032 is design only. It supports:

```text
adapter route is specified;
smoke workload scope is bounded;
proxy semantics are explicitly labeled;
M2033 artifact contract is defined.
```

It does not support:

```text
reset validity;
rollout validity;
controller-family ranking;
finite-window-vs-GRU conclusion;
paper-level benchmark evidence;
level3 self-identification.
```

## Next

M2033 should implement and run only the no-reset materialization preflight. It
must not reset the environment, execute policy actions, train, replay, rank
controller families, or claim paper/self-ID evidence.
