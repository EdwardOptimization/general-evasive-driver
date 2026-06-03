# M2493 Engineering Controller Source-Only Role Metric Panel

- status: completed
- result_class: `engineering_controller_source_only_role_metric_panel_pass`
- manifest: `experiments/manifests/m2493-engineering-controller-source-only-role-metric-panel.json`
- implementation: `src/autodrift/hf0_source_only_role_metric_panel.py`
- tests: `tests/test_hf0_source_only_role_metric_panel.py`
- summary: `runs/m2493_engineering_controller_source_only_role_metric_panel/summary.json`
- telemetry rows: `runs/m2493_engineering_controller_source_only_role_metric_panel/telemetry_rows.csv`
- role metric panel: `runs/m2493_engineering_controller_source_only_role_metric_panel/role_metric_panel.csv`
- next milestone: `m2494-engineering-controller-source-only-role-metric-panel-result-audit`
- external high-fidelity simulation installed/imported/executed in M2493: `false`
- measured validation/training/replay/PPO/ranking/winner/success-rate verdict in M2493: `false`
- paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Implementation

M2493 adds a source-only engineering telemetry panel over the same admitted
checkpoint and the same three admitted `FourWheelHF0Backend` fixtures selected
by M2492.

The implementation reuses the existing checkpoint admission gate:

```text
checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
checkpoint_admitted: true
checkpoint_obs_dim: 72
checkpoint_action_dim: 3
checkpoint_actor_encoder: human_view_online_gru
checkpoint_action_sequence_horizon: 1
```

The new module writes:

```text
summary.json
telemetry_rows.csv
role_metric_panel.csv
```

The telemetry rows record deployable action/path diagnostics only:

```text
fixture_id
surface_id
role_family
step_index
observation_shape
action_shape
action_steer/action_throttle/action_brake
action_finite/action_within_bounds/action_saturated
backend_status
terminated_by_backend/truncated_by_backend
diagnostic_wheel_force_count
state_x/state_y/state_psi
state_vx/state_vy/state_speed/state_yaw_rate
physical_steer/physical_throttle/physical_brake
policy_action
```

It does not record a success label, reward term, TTC, required clearance,
controller-family score, winner, or validation verdict.

## Run Result

Command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.hf0_source_only_role_metric_panel --checkpoint runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt --output-dir runs/m2493_engineering_controller_source_only_role_metric_panel --horizon-steps 100
```

Summary:

```text
result_class: engineering_controller_source_only_role_metric_panel_pass
status_pass: true
backend_id: source_only_four_wheel_hf0
fixture_count: 3
reset_count: 3
step_count: 300
expected_step_count: 300
horizon_steps_per_fixture: 100
role_metric_panel_row_count: 3
role_panel_covers_expected_roles: true
panel_rows_are_diagnostic_only: true
diagnostic_only_panel: true
```

Role counts:

```text
stable_aes: 100
drift_required_recovery: 100
unavoidable_mitigation: 100
```

Path and contract gates:

```text
all_reset_observations_shape_72: true
all_step_observations_shape_72: true
all_action_shapes_3: true
all_actions_finite: true
all_actions_within_bounds: true
all_backend_statuses_running: true
all_diagnostic_wheel_force_counts_4: true
max_action_saturation_fraction: 0.0
min_backend_alive_fraction: 1.0
min_bounded_action_fraction: 1.0
```

Actor-input leak flags:

```text
fixture_labels_enter_actor_input: false
scenario_labels_enter_actor_input: false
feasibility_classes_enter_actor_input: false
hidden_values_enter_actor_input: false
oracle_labels_enter_actor_input: false
diagnostics_available_to_actor: false
reward_terms_enter_actor_input: false
success_labels_enter_actor_input: false
ttc_enter_actor_input: false
required_clearance_enter_actor_input: false
```

Blocked execution/claim flags:

```text
external_high_fidelity_imported: false
high_fidelity_simulation_run: false
measured_validation_run: false
training_run: false
replay_run: false
ppo_run: false
ranking_run: false
winner_selected: false
checkpoint_promoted: false
success_rate_computed: false
controller_family_verdict_computed: false
driver_performance_claim_made: false
verdict_claim_made: false
paper_claim_made: false
finite_window_vs_gru_claim_made: false
level3_self_id_claim_made: false
current_sim_verdict_claim_made: false
high_fidelity_validation_claim_made: false
```

## Role Metric Panel

All three roles have the same panel values:

```text
step_count: 100
backend_alive_fraction: 1.0
finite_action_fraction: 1.0
bounded_action_fraction: 1.0
saturated_action_fraction: 0.0
observation_shape_72_fraction: 1.0
action_shape_3_fraction: 1.0
wheel_count_4_fraction: 1.0
terminated_fraction: 0.0
truncated_fraction: 0.0
speed_min: 6.068901928035857
speed_max: 7.989062669715224
speed_mean: 6.775584136692145
abs_y_max: 8.400292684739982
yaw_rate_min: 0.06864836552894436
yaw_rate_max: 0.9631033560959856
abs_yaw_rate_max: 0.9631033560959856
steer_min: 0.6422094106674194
steer_max: 0.9725109934806824
throttle_min: -0.8128403425216675
throttle_max: -0.06123323366045952
brake_min: -0.5082072019577026
brake_max: 0.09666210412979126
diagnostic_only: true
success_rate_computed: false
verdict_claim_made: false
```

## Interpretation

M2493 passes as an infrastructure milestone: the repository can now produce a
source-only telemetry table and a nonverdict role metric panel from the admitted
actor without changing the actor input or action contract.

The important negative signal is that the three role panels are numerically
identical. This is not evidence that the actor behaves equally well across
roles. It means the current source-only fixture rows still use role and fixture
identity as metadata while the local four-wheel backend reset path does not yet
materialize role-specific initial state, road geometry, obstacle state, or
vehicle/fault parameter differences.

M2493 therefore exposes an engineering blocker:

```text
source-only role fixture dynamics are not differentiated enough for role-level
behavior interpretation.
```

This is useful route evidence, but it is not driver-performance evidence.

## Supported Claim

Supported:

```text
The engineering-controller route now has an executable source-only role metric
panel that records deployable closed-loop telemetry and nonverdict aggregate
diagnostics over three admitted source-only fixtures.
```

Also supported:

```text
The admitted recurrent actor preserves the 72-observation / 3-action contract
for 100 deterministic policy-action steps per admitted fixture, with all path
gates and actor-input leak gates passing.
```

## Rejected Interpretations

M2493 does not support:

```text
driver performance
role-specific success or recovery quality
success-rate improvement
controller-family ranking
winner selection
checkpoint promotion
high-fidelity validation readiness
current-sim benchmark verdict
paper-level evidence
finite-window-vs-GRU conclusion
level3 self-identification
```

The role panel is diagnostic-only. The identical role values actively block any
claim that the current source-only fixtures are measuring differentiated role
behavior.

## Failure Taxonomy

Observed:

```text
scenario_sampling_failure / fixture_differentiation_gap:
  active for role interpretation. The role labels do not yet produce different
  source-only dynamics or obstacle/road situations.
```

Controlled:

```text
contract_violation:
  controlled. Checkpoint admission and all observation/action shape gates pass.

lineage_invalid:
  controlled. M2493 artifacts are written under the manifest-defined run dir.

metric_artifact:
  controlled if the panel remains diagnostic-only. Risk becomes high if the
  identical role panel is treated as a performance or role-capability result.
```

Unresolved:

```text
behavior_regression:
  not assessed. There is no baseline controller or previous actor comparison.

objective_overfit:
  medium. The panel adds real telemetry, but another metric-only step would be
  low-value unless it repairs role fixture differentiation or audits the result.
```

## Next Route

M2493 routes to result audit:

```text
m2494-engineering-controller-source-only-role-metric-panel-result-audit
```

The audit should accept the infrastructure path only with the claim boundary
above, explicitly classify the identical role panel as a fixture
differentiation blocker, and choose a bounded follow-up. The likely useful
follow-up is a source-only role fixture parameterization design, not another
plain metric-panel extension and not a performance claim.
