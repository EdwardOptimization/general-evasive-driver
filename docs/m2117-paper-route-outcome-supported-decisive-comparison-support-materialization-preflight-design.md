# M2117 Paper-Route Outcome-Supported Decisive Comparison-Support Materialization Preflight Design

- status: completed
- decision: `comparison_support_materialization_preflight_design_admit_implementation`
- parent artifact: `configs/paper_route_outcome_supported_decisive_comparison_support_candidates_v0.json`
- reset/rollout/measured execution in M2117: `false`
- policy actions executed in M2117: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Principle

M2117 freezes a reset-free materialization preflight. Its job is only to turn
audited comparison-support candidates into concrete executable-spec metadata
and planned workload rows. It must not test reset validity, execute policy
actions, compare controller families, or label rows as paper-valid.

```text
candidate generation -> materialization preflight -> reset validation -> measured execution -> localization -> support gate -> comparison decision
```

Only the first arrow is designed here.

## Input

M2118 must read:

```text
configs/paper_route_outcome_supported_decisive_comparison_support_candidates_v0.json
```

Expected input invariants:

```text
candidate_count: 240
intent groups: 4 x 60
paper_validity_claim_true_count: 0
profile_specific_tuning_true_count: 0
actor_input_forbidden_key_count: 0
guardrail_violation_count: 0
```

## Candidate-To-Spec Mapping

Each candidate becomes exactly one executable spec:

```text
task_source_id       := m2118-cs-{candidate_id}
panel_source_id      := candidate_id
candidate_id         := candidate_id
panel_task_family    := source_family
source_origin        := m2115_comparison_support_candidate_generation
source_kind          := source_kind
source_edge          := difficulty_axis
window_tag           := comparison_support_intent
source_role_semantics:= target_support_tier
source_reference     := candidate_id
materialization_semantics := comparison_support_smoke_proxy
generated_source_row := true
paper_validity_claim := false
profile_specific_tuning := false
```

The following candidate fields must be preserved in both spec and workload
rows:

```text
scenario_redesign_branch
comparison_support_intent
target_support_tier
dynamics_band
obstacle_timing_band
road_width_band
initial_speed_band
actor_input_contract
paper_validity_claim
profile_specific_tuning
controller_family_ranking_claim_made
finite_window_vs_gru_conclusion_made
paper_level_claim_made
level3_self_id_claim_made
```

## Proxy Template Mapping

M2118 may use existing P0-compatible hook templates through
`env_config_for_hook_spec`, but the mapping must be deterministic and
candidate-level, never profile-specific.

```text
source_kind contains actuator_delay
  -> t4_actuator_delay_response

source_kind contains boundary or near_zero_margin
  -> t5_boundary_axis_retarget

comparison_support_intent == collision_relief_probe
  -> t5_near_boundary_warmup

comparison_support_intent == discriminative_boundary
  -> t5_near_boundary_warmup, unless the source_kind rules above override it

otherwise
  -> t4_staged_warmup_capability
```

Reveal-step mapping is also deterministic:

```text
early  -> 72 + 4 * (candidate_index % 5)
medium -> 96 + 4 * (candidate_index % 5)
late   -> 120 + 4 * (candidate_index % 5)
```

The env config must satisfy the current human-view actor contract:

```text
history_length >= 1
action_history_mode == full
include_privileged_params == false
wheel_observation_mode == none
obstacle_relative_velocity_mode == zero
```

## Workload Mapping

M2118 should create a bounded 5-profile workload, not the full 12-profile
matrix:

```text
L0_current_masked
L1_one_step
L2_window_50
L3_online_gru
L3_reset_control_corrected
```

Expected workload size:

```text
240 executable specs x 5 profiles = 1200 planned workload rows
```

Each workload row must keep:

```text
environment_rollout_scheduled=false
training_scheduled=false
profile_specific_tuning=false
controller_family_ranking_claim_made=false
finite_window_vs_gru_conclusion_made=false
paper_level_claim_made=false
level3_self_id_claim_made=false
```

## Planned Outputs

M2118 must write:

```text
runs/m2118_paper_route_outcome_supported_decisive_comparison_support_materialization_preflight/summary.json
runs/m2118_paper_route_outcome_supported_decisive_comparison_support_materialization_preflight/executable_task_specs.json
runs/m2118_paper_route_outcome_supported_decisive_comparison_support_materialization_preflight/executable_task_specs.csv
runs/m2118_paper_route_outcome_supported_decisive_comparison_support_materialization_preflight/planned_workload.csv
runs/m2118_paper_route_outcome_supported_decisive_comparison_support_materialization_preflight/profile_artifacts.csv
runs/m2118_paper_route_outcome_supported_decisive_comparison_support_materialization_preflight/materialization_failures.csv
runs/m2118_paper_route_outcome_supported_decisive_comparison_support_materialization_preflight/aggregate_by_intent.csv
runs/m2118_paper_route_outcome_supported_decisive_comparison_support_materialization_preflight/aggregate_by_proxy_template_family.csv
runs/m2118_paper_route_outcome_supported_decisive_comparison_support_materialization_preflight/claim_boundary.csv
```

## Preflight Pass Gates

M2118 passes only if:

```text
result_class == comparison_support_materialization_preflight_pass
candidate_count == 240
executable_spec_count == 240
workload_row_count == 1200
profile_count == 5
materialization_failure_count == 0
missing_profile_artifact_count == 0
contract_violation_count == 0
paper_validity_claim_true_count == 0
profile_specific_tuning_true_count == 0
guardrail_violation_count == 0
```

No reset-validity claim is allowed. A clean M2118 only admits a reset-validation
command design.

## Next

Next milestone:

```text
m2118-paper-route-outcome-supported-decisive-comparison-support-materialization-preflight-implementation
```
