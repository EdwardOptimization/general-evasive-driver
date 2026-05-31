# M2062 Paper-Route Outcome-Supported Decisive Materialization Design

- status: completed
- decision: `outcome_supported_decisive_materialization_design_admit_no_reset_preflight_implementation`
- branch: `paper_route_outcome_supported_decisive_task_distribution`
- source artifact: `configs/paper_route_outcome_supported_decisive_task_candidates_v0.json`
- reset/rollout/measured execution in M2062: `false`
- policy actions executed in M2062: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Purpose

M2062 freezes the bridge from the M2060 no-rollout candidate artifact to an
executable reset-validation substrate. This milestone is design only. It must
not run reset, rollout, measured execution, training, replay, PPO, or ranking.

M2032/M2048 showed that materialization must preserve provenance and claim
guards. M2062 keeps that discipline, but does not reuse the old parent-repair
logic. M2060 candidates are a new smoke-proxy candidate set, so M2063 should
generate executable specs directly from candidate metadata.

## Scope

Materialize all M2060 candidates:

```text
candidate count: 240
family quotas: 48 / 60 / 60 / 36 / 36
split quotas: public_debug 144 / public_gate 96 / private_holdout 0
```

Profile scope for the first materialized workload is the sentinel smoke set:

```text
L0_current_masked
L1_one_step
L2_window_50
L3_online_gru
L3_reset_control_corrected
```

Expected workload:

```text
240 executable specs x 5 sentinel profiles = 1200 workload rows
```

Do not materialize the full 12-profile matrix yet. Full comparison remains
blocked until reset validation and outcome-support measured smoke pass.

## Output Schema

M2063 should write:

```text
runs/m2063_paper_route_outcome_supported_decisive_materialization_preflight/summary.json
runs/m2063_paper_route_outcome_supported_decisive_materialization_preflight/executable_task_specs.json
runs/m2063_paper_route_outcome_supported_decisive_materialization_preflight/executable_task_specs.csv
runs/m2063_paper_route_outcome_supported_decisive_materialization_preflight/planned_sentinel_workload.csv
runs/m2063_paper_route_outcome_supported_decisive_materialization_preflight/profile_artifacts.csv
runs/m2063_paper_route_outcome_supported_decisive_materialization_preflight/family_axis_aggregate.csv
runs/m2063_paper_route_outcome_supported_decisive_materialization_preflight/source_kind_aggregate.csv
runs/m2063_paper_route_outcome_supported_decisive_materialization_preflight/materialization_failures.csv
runs/m2063_paper_route_outcome_supported_decisive_materialization_preflight/claim_boundary.csv
```

### Executable Spec Fields

Each executable spec must preserve M2060 provenance:

```text
task_source_id
candidate_id
candidate_set_id
branch_id
panel_task_family
source_split
source_origin
source_kind
source_edge
window_tag
source_reference
task_role_semantics
obstacle_distance_band
road_width_band
curvature_band
dynamics_band
initial_speed_band
same_current_constraint
history_intervention_candidate
warmup_mode
warmup_duration_seconds
obstacle_reveal_delay_seconds
recent_window_seconds
older_history_offset_seconds
diagnostic_delay_seconds
terminal_margin_bucket
materialization_semantics
proxy_template_family
generated_source_row
paper_validity_claim
profile_specific_tuning
controller_family_ranking_claim_made
finite_window_vs_gru_conclusion_made
paper_level_claim_made
level3_self_id_claim_made
contract_checks
contract_violation_count
env_config
```

### Workload Fields

Each workload row crosses one executable spec with one sentinel profile:

```text
workload_id
task_source_id
candidate_id
panel_task_family
source_split
profile_name
profile_config_path
checkpoint_path
source_kind
source_edge
window_tag
materialization_semantics
paper_validity_claim
environment_rollout_scheduled
training_scheduled
profile_specific_tuning
controller_family_ranking_claim_made
finite_window_vs_gru_conclusion_made
paper_level_claim_made
level3_self_id_claim_made
```

## Smoke-Proxy Env Config Recipe

M2063 should use the existing human-view no-wheel obstacle task contract:

```text
include_privileged_params = false
wheel_observation_mode = none
action_history_mode = full
obstacle_relative_velocity_mode = zero
history_length >= 1
obstacle.enabled = true
friction_limited_speed = true
```

Axis mapping:

```text
obstacle_distance_band:
  early  -> obstacle.distance_range [52.0, 70.0]
  medium -> obstacle.distance_range [34.0, 52.0]
  late   -> obstacle.distance_range [18.0, 36.0]

road_width_band:
  generous -> track_width 7.0
  nominal  -> track_width 5.5
  tight    -> track_width 4.4

curvature_band:
  straight_or_low -> track_kind circle, track_radius 60.0
  moderate        -> track_kind circle, track_radius 32.0
  high            -> track_kind circle, track_radius 18.0

dynamics_band:
  nominal_mu     -> randomization.mu_range [0.75, 1.05]
  low_mu         -> randomization.mu_range [0.35, 0.55]
  mixed_mu       -> randomization.mu_range [0.28, 1.05]
  actuator_delay -> randomization.actuator_tau_scale_range [1.8, 2.8]

initial_speed_band:
  low     -> speed_range [7.0, 11.0]
  nominal -> speed_range [10.0, 15.0]
  high    -> speed_range [14.0, 20.0]
```

Family metadata should affect warmup/reveal settings, but not actor inputs:

```text
T1:
  warmup_gate may be disabled or neutral.

T2:
  preserve same_current_constraint and recent/older-history metadata.
  The materialized smoke proxy does not prove same-current matching yet.

T3:
  enable warmup_gate with candidate warmup_mode, duration, and reveal delay.

T4:
  enable warmup_gate and preserve diagnostic_delay_seconds.

T5:
  preserve terminal_margin_bucket and use tighter obstacle/road settings only
  within the configured axis bounds.
```

Hidden dynamics metadata is allowed in `env_config`; it must not enter
`actor_input_fields`.

## Contract Checks

M2063 must fail closed on:

```text
missing candidate fields
duplicate task_source_id
duplicate workload_id
sentinel profile config/checkpoint missing
family quota mismatch
split quota mismatch
difficulty-axis coverage loss
contract_violation_count > 0
materialization_semantics != smoke_proxy
paper_validity_claim = true
profile_specific_tuning = true
controller_family_ranking_claim_made = true
finite_window_vs_gru_conclusion_made = true
paper_level_claim_made = true
level3_self_id_claim_made = true
environment reset/rollout scheduled in preflight
```

## Result Classes

Expected pass:

```text
outcome_supported_decisive_materialization_preflight_pass:
  executable_spec_count = 240
  planned_sentinel_workload_count = 1200
  sentinel_profile_count = 5
  family quotas match 48/60/60/36/36
  split quotas match 144/96/0
  materialization_failure_count = 0
  contract_violation_count = 0
  guardrail_violation_count = 0
```

Other classes:

```text
outcome_supported_decisive_materialization_preflight_partial
outcome_supported_decisive_materialization_preflight_fail_closed
```

## Next

M2063 should implement the no-reset materialization preflight with focused
tests. Reset validation, rollout, measured execution, ranking,
finite-window-vs-GRU conclusions, paper-level comparison, and level3 self-ID
claims remain blocked.
