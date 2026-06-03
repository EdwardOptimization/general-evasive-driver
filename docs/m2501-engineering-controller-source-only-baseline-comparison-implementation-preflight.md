# M2501 Engineering Controller Source-Only Baseline Comparison Implementation Preflight

- status: completed
- result_class: `engineering_controller_source_only_baseline_comparison_preflight_pass`
- manifest: `experiments/manifests/m2501-engineering-controller-source-only-baseline-comparison-implementation-preflight.json`
- implementation: `src/autodrift/hf0_source_only_baseline_comparison_panel.py`
- design source: `docs/m2500-engineering-controller-source-only-baseline-comparison-design.md`
- summary: `runs/m2501_engineering_controller_source_only_baseline_comparison_preflight/summary.json`
- telemetry rows: `runs/m2501_engineering_controller_source_only_baseline_comparison_preflight/telemetry_rows.csv`
- controller-role metric panel: `runs/m2501_engineering_controller_source_only_baseline_comparison_preflight/controller_role_metric_panel.csv`
- next milestone: `m2502-engineering-controller-source-only-baseline-comparison-result-audit`
- external high-fidelity simulation installed/imported/executed in M2501: `false`
- measured validation/training/replay/PPO/ranking/winner/success-rate verdict in M2501: `false`
- paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Implementation

M2501 implements the M2500 bounded source-only comparison protocol. It compares
the admitted checkpoint against two fixed deployed-action baselines on the same
three M2496 parameterized source-only role fixtures.

Comparison subjects:

```text
m1154_policy_actor:
  checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
  policy_action: true

coast_open_loop:
  normalized action: [0.0, -1.0, -1.0]
  physical control: steer 0.0 throttle 0.0 brake 0.0
  policy_action: false

straight_full_brake_open_loop:
  normalized action: [0.0, -1.0, 1.0]
  physical control: steer 0.0 throttle 0.0 brake 1.0
  policy_action: false
```

Command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.hf0_source_only_baseline_comparison_panel --checkpoint runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt --output-dir runs/m2501_engineering_controller_source_only_baseline_comparison_preflight --horizon-steps 100 --milestone m2501-engineering-controller-source-only-baseline-comparison-implementation-preflight --next-blocker m2502-engineering-controller-source-only-baseline-comparison-result-audit
```

## Run Result

Summary:

```text
result_class: engineering_controller_source_only_baseline_comparison_preflight_pass
status_pass: true
comparison_subject_count: 3
comparison_subjects:
  m1154_policy_actor
  coast_open_loop
  straight_full_brake_open_loop
role_count: 3
reset_count / expected_reset_count: 9 / 9
telemetry_row_count / expected_telemetry_row_count: 900 / 900
role_subject_panel_row_count / expected_role_subject_panel_row_count: 9 / 9
horizon_steps_per_role_subject: 100
```

Checkpoint admission:

```text
checkpoint_admitted: true
checkpoint_obs_dim: 72
checkpoint_action_dim: 3
checkpoint_actor_encoder: human_view_online_gru
checkpoint_action_sequence_horizon: 1
```

Reset digest gates:

```text
role_reset_digests_match_across_subjects: true
role_reset_digests_differentiated: true
unique_role_reset_observation_digest_count: 3
stable_aes: be74fec0227f041e
drift_required_recovery: ca4fed8c6285ef14
unavoidable_mitigation: eff1d7f164d537cb
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
panel_rows_are_diagnostic_only: true
all_rows_are_diagnostic_only: true
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

## Diagnostic Panel

M2501 writes nine role-subject rows. Selected nonverdict metrics:

```text
coast_open_loop / stable_aes:
  speed_min/max/mean: 8.85917322634564 / 8.998634481836683 / 8.928792393335469
  abs_y_max: 0.012651451147566635
  abs_yaw_rate_max: 0.010736374575436913

coast_open_loop / drift_required_recovery:
  speed_min/max/mean: 9.855986121622037 / 10.008773986182113 / 9.930047672466369
  abs_y_max: 1.5224170327486037
  abs_yaw_rate_max: 0.16457386345149902

coast_open_loop / unavoidable_mitigation:
  speed_min/max/mean: 8.067847954427778 / 8.203475984064163 / 8.134375207334614
  abs_y_max: 0.9934866503903942
  abs_yaw_rate_max: 0.11629036815108763

m1154_policy_actor / stable_aes:
  speed_min/max/mean: 6.666369687068979 / 8.99013590634997 / 7.630554099162932
  abs_y_max: 8.874552706111096
  abs_yaw_rate_max: 0.8605756585238477

m1154_policy_actor / drift_required_recovery:
  speed_min/max/mean: 7.552493285353232 / 10.00564010918318 / 8.55781958899384
  abs_y_max: 9.186174406522152
  abs_yaw_rate_max: 0.5901673537563995

m1154_policy_actor / unavoidable_mitigation:
  speed_min/max/mean: 5.082710510108602 / 8.192833102998442 / 6.346678404234831
  abs_y_max: 4.35557577943488
  abs_yaw_rate_max: 0.7285742891752022

straight_full_brake_open_loop / stable_aes:
  speed_min/max/mean: 0.774325698362291 / 8.971049507356648 / 4.920379757919863
  abs_y_max: 0.007579618540843539
  abs_yaw_rate_max: 0.010730171095244203

straight_full_brake_open_loop / drift_required_recovery:
  speed_min/max/mean: 1.7728784172051988 / 9.981256386344572 / 5.922791731158318
  abs_y_max: 1.1072709005079189
  abs_yaw_rate_max: 0.1655293441659917

straight_full_brake_open_loop / unavoidable_mitigation:
  speed_min/max/mean: 0.016206439311665655 / 8.175940320090522 / 4.1257582510455855
  abs_y_max: 0.6887851573471163
  abs_yaw_rate_max: 0.11740453932066494
```

These rows are diagnostic-only. They are not a ranking and do not select a
controller winner.

## Supported Claim

Supported:

```text
The source-only HF0 comparison panel can generate bounded diagnostic telemetry
across the admitted policy actor and two open-loop action baselines on the same
parameterized role fixtures while preserving the deployed actor/action contract.
```

## Rejected Interpretations

M2501 does not support:

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

The next step must audit the comparison artifacts before any follow-up claim,
repair, or synthesis.

## Next Route

M2501 routes to:

```text
m2502-engineering-controller-source-only-baseline-comparison-result-audit
```
