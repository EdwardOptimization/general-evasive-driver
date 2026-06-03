# M2498 Engineering Controller Parameterized Source-Only Role Metric Panel Rerun

- status: completed
- result_class: `engineering_controller_parameterized_source_only_role_metric_panel_pass`
- manifest: `experiments/manifests/m2498-engineering-controller-parameterized-source-only-role-metric-panel-rerun.json`
- implementation: `src/autodrift/hf0_source_only_role_metric_panel.py`
- parameterization source: `src/autodrift/hf0_source_only_role_fixture_parameterization.py`
- summary: `runs/m2498_engineering_controller_parameterized_source_only_role_metric_panel/summary.json`
- telemetry rows: `runs/m2498_engineering_controller_parameterized_source_only_role_metric_panel/telemetry_rows.csv`
- role metric panel: `runs/m2498_engineering_controller_parameterized_source_only_role_metric_panel/role_metric_panel.csv`
- next milestone: `m2499-engineering-controller-parameterized-source-only-role-metric-panel-result-audit`
- external high-fidelity simulation installed/imported/executed in M2498: `false`
- measured validation/training/replay/PPO/ranking/winner/success-rate verdict in M2498: `false`
- paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Implementation

M2498 reruns the source-only role metric panel on the M2496 parameterized role
fixtures. The panel path is still the M2493 nonverdict telemetry pipeline, but
now `--use-parameterized-role-fixtures` supplies differentiated reset specs to
`FourWheelHF0Backend`.

The default M2493 path remains available. Parameterized fixtures are opt-in.

Command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.hf0_source_only_role_metric_panel --checkpoint runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt --output-dir runs/m2498_engineering_controller_parameterized_source_only_role_metric_panel --horizon-steps 100 --use-parameterized-role-fixtures --milestone m2498-engineering-controller-parameterized-source-only-role-metric-panel-rerun --next-blocker m2499-engineering-controller-parameterized-source-only-role-metric-panel-result-audit
```

## Run Result

Summary:

```text
result_class: engineering_controller_parameterized_source_only_role_metric_panel_pass
status_pass: true
parameterized_role_fixtures: true
all_rows_use_parameterized_fixtures: true
fixture_count: 3
reset_count: 3
step_count: 300
expected_step_count: 300
horizon_steps_per_fixture: 100
role_metric_panel_row_count: 3
role_panel_covers_expected_roles: true
```

Checkpoint admission:

```text
checkpoint_admitted: true
checkpoint_obs_dim: 72
checkpoint_action_dim: 3
checkpoint_actor_encoder: human_view_online_gru
checkpoint_action_sequence_horizon: 1
```

Role reset digests:

```text
stable_aes: be74fec0227f041e
drift_required_recovery: ca4fed8c6285ef14
unavoidable_mitigation: eff1d7f164d537cb
unique_role_reset_observation_digest_count: 3
role_reset_observation_digests_differentiated: true
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

M2498 fixes the M2493 identical-role panel problem. The role metrics now differ
because the reset fixtures are dynamically parameterized.

Selected nonverdict role metrics:

```text
stable_aes:
  speed_min/max/mean: 6.666369687068979 / 8.99013590634997 / 7.630554099162932
  abs_y_max: 8.874552706111096
  abs_yaw_rate_max: 0.8605756585238477
  steer_min/max: 0.6655488610267639 / 0.9733885526657104
  throttle_min/max: -0.8038698434829712 / -0.058990806341171265
  brake_min/max: -0.5361865162849426 / 0.15904149413108826

drift_required_recovery:
  speed_min/max/mean: 7.552493285353232 / 10.00564010918318 / 8.55781958899384
  abs_y_max: 9.186174406522152
  abs_yaw_rate_max: 0.5901673537563995
  steer_min/max: 0.8314849734306335 / 0.9719889163970947
  throttle_min/max: -0.8009517192840576 / -0.10030572861433029
  brake_min/max: -0.4674830436706543 / 0.05517961457371712

unavoidable_mitigation:
  speed_min/max/mean: 5.082710510108602 / 8.192833102998442 / 6.346678404234831
  abs_y_max: 4.35557577943488
  abs_yaw_rate_max: 0.7285742891752022
  steer_min/max: 0.7035594582557678 / 0.9707010388374329
  throttle_min/max: -0.8671594858169556 / -0.6142643094062805
  brake_min/max: -0.3988198935985565 / -0.1679658144712448
```

Every role panel row remains diagnostic-only:

```text
backend_alive_fraction: 1.0
finite_action_fraction: 1.0
bounded_action_fraction: 1.0
saturated_action_fraction: 0.0
observation_shape_72_fraction: 1.0
action_shape_3_fraction: 1.0
wheel_count_4_fraction: 1.0
terminated_fraction: 0.0
truncated_fraction: 0.0
diagnostic_only: true
success_rate_computed: false
verdict_claim_made: false
```

## Supported Claim

Supported:

```text
The source-only role metric panel can now run on dynamically differentiated
source-only fixtures and produce nonidentical role telemetry while preserving
the deployed actor/action contract.
```

This is engineering-controller telemetry evidence. It is stronger than M2493
because the role fixtures are no longer metadata-only.

## Rejected Interpretations

M2498 does not support:

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

No success metric or external validation backend was used. The result must be
audited before any further claim escalation.

## Failure Taxonomy

Resolved:

```text
scenario_sampling_failure / source_only_role_fixture_differentiation_blocker:
  resolved for the source-only nonverdict role metric panel path. Role reset
  digests are differentiated and role metrics are no longer identical.
```

Controlled:

```text
contract_violation:
  controlled. Checkpoint admission and all observation/action gates pass.

metric_artifact:
  controlled. The panel remains diagnostic-only and rejects success-rate or
  performance interpretation.

lineage_invalid:
  controlled. M2496/M2497 parameterization evidence and M2498 panel artifacts
  are linked by manifest.
```

Unresolved:

```text
behavior_regression:
  not assessed. No baseline controller or actor comparison ran.

objective_overfit:
  medium. M2498 adds real differentiated telemetry, but a result audit must
  decide whether the branch should run an audited comparison, repair, or
  synthesize.
```

## Next Route

M2498 routes to:

```text
m2499-engineering-controller-parameterized-source-only-role-metric-panel-result-audit
```

The audit should verify M2498 artifacts, classify the nonidentical role metrics
as engineering diagnostics only, and decide whether the next route is an
audited source-only baseline comparison, a repair, or branch synthesis.
