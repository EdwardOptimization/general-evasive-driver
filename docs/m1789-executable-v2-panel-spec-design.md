# M1789 Executable V2 Panel Spec Design

- status: completed
- decision: `executable_v2_panel_spec_design_admit_materialization_preflight`
- source: `docs/m1788-role-specific-panel-metric-repair-materialization-result-audit.md`
- no reset: true
- no rollout: true
- training/replay/PPO: false

## Summary

M1789 defines the reset-ready schema needed between the M1787 v2 contract and a
future reset feasibility preflight. M1788 found the v2 contract complete but not
executable. This design closes that gap by specifying how each v2 role surface
becomes a concrete scenario spec with seeds, reusable M1771 fields, label
balance, hidden-bucket balance, and metric contracts.

M1789 does not run reset or rollout. It only defines the executable schema and
materialization rules for the next no-rollout preflight.

## Reusable M1771 Fields

The v2 executable spec should reuse these M1771 bounded-panel fields:

```text
bounded_panel_spec_id
role_panel_id
role_panel_label
scenario_family_id
scenario_family
scenario_role
profile_name
profile_config_path
checkpoint_path
config_exists
checkpoint_exists
hidden_dynamics_bucket
road_boundary_bucket
obstacle_timing_bucket
obstacle_lateral_bucket
allowed_labels_metadata_only
labels_enter_actor_input
diagnostic_only_no_ranking_claim
ranking_eligible_after_audit
environment_reset_scheduled
environment_rollout_scheduled
training_scheduled
profile_specific_tuning
env_config
```

Those fields already encode the no-privileged-input and no-ranking guardrails
and are compatible with the M1777 execution adapter.

## New V2 Fields

The executable v2 spec adds these fields:

```text
v2_panel_spec_id
v2_role_surface_id
v2_task_label
v2_hidden_bucket_family
v2_primary_metric
v2_primary_metric_direction
v2_supporting_metrics
v2_admissibility_gate
v2_ranking_admissible_by_default
v2_preserves_profile_controls
v2_requires_new_materialization
v2_sampler_config
v2_env_config_delta
v2_expected_label_balance_group
v2_expected_hidden_bucket_balance_group
v2_recovery_horizon_required
v2_claim_boundary_id
reset_ready_spec
```

The key distinction is that `role_surface_id` is not only a scorecard label. It
also controls how labels, hidden buckets, scenario families, and metric
contracts are materialized.

## Role Surface Mapping

### stable_avoidance_aes

Source role:

```text
M1771 role_panel_id: stable_avoidance_aes
allowed labels: aeb_feasible; aes_feasible
hidden buckets: nominal; brake_variation; friction_step
```

V2 executable rules:

```text
v2_role_surface_id: stable_avoidance_aes
v2_task_label: aeb_feasible|aes_feasible
v2_admissibility_gate: collision_rate_low_and_off_track_rate_low
v2_primary_metric: admissible_obstacle_pass_rate
reset_ready_spec: true
```

Materialization must keep AEB-feasible and AES-feasible cells separately
countable. Road-boundary buckets must include nominal/moderate and at least one
tighter boundary stress bucket.

### drift_required_recovery

Source role:

```text
M1771 role_panel_id: drift_required_recovery
allowed label: drift_required
hidden buckets: friction_step; low_mu; tire_stiffness
```

V2 executable rules:

```text
v2_role_surface_id: drift_required_recovery
v2_task_label: drift_required
v2_admissibility_gate: obstacle_clearance_and_post_maneuver_recovery_observed
v2_primary_metric: controlled_recovery_stage_pass_rate
v2_recovery_horizon_required: true
reset_ready_spec: true
```

Materialization must include a recovery horizon and staged event fields. Drift
usage is diagnostic; it is not the objective.

### hidden_robust_aes_feasible

Source role:

```text
M1771 role_panel_id: hidden_dynamics_robustness
allowed label: aes_feasible
hidden buckets: actuator_delay; brake_drive_variation; mass_cg_shift
```

V2 executable rules:

```text
v2_role_surface_id: hidden_robust_aes_feasible
v2_task_label: aes_feasible
v2_admissibility_gate: label_pure_hidden_bucket_balance
v2_primary_metric: worst_hidden_bucket_success_rate
reset_ready_spec: true
```

### hidden_robust_drift_required

Source role:

```text
M1771 role_panel_id: hidden_dynamics_robustness
allowed label: drift_required
hidden buckets: actuator_delay; brake_drive_variation; mass_cg_shift; low_mu; tire_stiffness; friction_step
```

V2 executable rules:

```text
v2_role_surface_id: hidden_robust_drift_required
v2_task_label: drift_required
v2_admissibility_gate: label_pure_hidden_bucket_balance
v2_primary_metric: worst_hidden_bucket_controlled_recovery_rate
v2_recovery_horizon_required: true
reset_ready_spec: true
```

### hidden_robust_unavoidable_mitigation

Source role:

```text
M1771 role_panel_id: hidden_dynamics_robustness
allowed label: unavoidable
hidden buckets: actuator_delay; brake_variation; low_mu; brake_drive_variation; mass_cg_shift
```

V2 executable rules:

```text
v2_role_surface_id: hidden_robust_unavoidable_mitigation
v2_task_label: unavoidable
v2_admissibility_gate: label_pure_hidden_bucket_balance
v2_primary_metric: worst_hidden_bucket_impact_severity_proxy_mean
reset_ready_spec: true
```

### unavoidable_mitigation

Source role:

```text
M1771 role_panel_id: unavoidable_mitigation
allowed label: unavoidable
hidden buckets: actuator_delay; brake_variation; low_mu
```

V2 executable rules:

```text
v2_role_surface_id: unavoidable_mitigation
v2_task_label: unavoidable
v2_admissibility_gate: mitigation_surface_only_no_avoidance_ranking
v2_primary_metric: impact_severity_proxy_mean
reset_ready_spec: true
```

Obstacle-pass success is not a primary metric for mitigation.

## Balancing Rules

The materializer should enforce these rules:

```text
profile controls:
  preserve all 12 M1783 profiles

role surfaces:
  materialize all 6 v2_role_surface_id values

labels:
  stable AES keeps aeb_feasible and aes_feasible countable
  drift recovery uses drift_required only
  hidden robustness is label-pure per v2 surface
  mitigation uses unavoidable only

hidden buckets:
  each v2 surface materializes its declared hidden_bucket_family
  hidden robustness reports worst bucket and bucket spread, not mixed average

ranking:
  v2_ranking_admissible_by_default is always false
  diagnostic_only_no_ranking_claim is always true

guardrails:
  labels_enter_actor_input is false
  environment_reset_scheduled is false for materialization
  environment_rollout_scheduled is false for materialization
  training_scheduled is false
  profile_specific_tuning is false
```

## Output Contract For M1790

M1790 should materialize these artifacts:

```text
summary.json
executable_v2_panel_specs.json
executable_v2_panel_specs.csv
executable_v2_panel_matrix.csv
v2_role_surface_summary.csv
v2_field_contract.csv
v2_reuse_mapping.csv
v2_claim_boundary.csv
```

The executable spec rows must include:

```text
v2_panel_spec_id
source_v1_bounded_panel_spec_id
v2_role_surface_id
role_panel_id
profile_name
profile_config_path
checkpoint_path
v2_task_label
allowed_labels_metadata_only
hidden_dynamics_bucket
road_boundary_bucket
obstacle_timing_bucket
obstacle_lateral_bucket
v2_primary_metric
v2_admissibility_gate
v2_sampler_config
v2_env_config_delta
env_config
reset_ready_spec
diagnostic_only_no_ranking_claim
v2_ranking_admissible_by_default
environment_reset_scheduled
environment_rollout_scheduled
training_scheduled
profile_specific_tuning
```

## Route Decision

Route to M1790 executable v2 panel spec materialization preflight. M1790 should
write reset-ready spec artifacts only. It should not run reset or rollout.

## Guardrails

- environment reset started: `false`
- environment rollout started: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- reset-ready executable v2 panel spec schema is defined;
- M1790 materialization preflight is admitted.

Unsupported:

- executable v2 spec materialization;
- reset feasibility;
- measured execution;
- controller-family ranking;
- profile promotion;
- private-holdout evidence;
- paper-level benchmark evidence;
- level3 self-identification.
