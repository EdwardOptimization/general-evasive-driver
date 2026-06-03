# M2508 Engineering Controller Runtime Inference Cost Report Preflight

- status: completed
- result_class: `engineering_controller_runtime_inference_cost_report_pass`
- manifest: `experiments/manifests/m2508-engineering-controller-runtime-inference-cost-report-preflight.json`
- implementation: `src/autodrift/engineering_controller_runtime_report.py`
- summary: `runs/m2508_engineering_controller_runtime_inference_cost_report/summary.json`
- runtime measurements: `runs/m2508_engineering_controller_runtime_inference_cost_report/runtime_measurements.csv`
- checkpoint: `runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt`
- next milestone: `m2509-engineering-controller-runtime-inference-cost-report-result-audit`
- external high-fidelity simulation installed/imported/executed in M2508: `false`
- environment rollout/simulator step/policy rollout in M2508: `false`
- measured validation/training/replay/PPO/ranking/winner selection in M2508: `false`
- paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Runtime Report

M2508 measures the admitted checkpoint's actor-only forward path:

```text
timed_path: recurrent_features_tensor_plus_actor_mean_tanh
synthetic_observation_source: seeded_normal_shape_only
device: cpu
batch sizes: 1, 8, 32
warmup iterations: 20
measured iterations per batch: 100
measurement rows: 300
```

This is an inference-cost report, not an environment rollout. The action outputs
are used only to check shape, finiteness, and bounds. They are not interpreted as
control behavior.

## Contract Gates

Accepted checkpoint and actor contract:

```text
checkpoint_admitted: true
checkpoint_obs_dim: 72
checkpoint_action_dim: 3
checkpoint_actor_encoder: human_view_online_gru
checkpoint_action_sequence_horizon: 1
model_parameter_count: 164679
checkpoint_file_size_bytes: 668277
```

Measurement gates:

```text
status_pass: true
measurement_row_count: 300
expected_measurement_row_count: 300
all_observation_shape_72: true
all_action_shape_3: true
all_actions_finite: true
all_actions_within_bounds: true
all_forward_times_positive: true
```

## Timing Summary

CPU timing from `summary.json`:

```text
batch 1:
  forward_time_us_mean: 45.05791
  forward_time_us_p50: 42.13
  per_sample_time_us_mean: 45.05791
  per_sample_time_us_p50: 42.13

batch 8:
  forward_time_us_mean: 81.34848
  forward_time_us_p50: 76.35499999999999
  per_sample_time_us_mean: 10.16856
  per_sample_time_us_p50: 9.544374999999999

batch 32:
  forward_time_us_mean: 128.59439
  forward_time_us_p50: 124.291
  per_sample_time_us_mean: 4.0185746875
  per_sample_time_us_p50: 3.88409375
```

These timings are local CPU measurements for a bounded actor forward path. They
are not simulator throughput, controller quality, or deployment certification.

## Blocked Execution And Claim Flags

```text
actor_forward_pass_run: true
environment_rollout_run: false
simulator_step_run: false
external_high_fidelity_simulation_included: false
policy_action_run: false
policy_rollout_run: false
action_outputs_interpreted_as_control: false
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

## Result

M2508 passes as a runtime/inference-cost report preflight. It fills a Route A
engineering artifact without extending the public-pack branch and without
running a simulator, policy rollout, training, ranking, success-rate, or
validation verdict.

## Next Route

Route to:

```text
m2509-engineering-controller-runtime-inference-cost-report-result-audit
```

M2509 should audit the runtime report artifacts before any deployability claim,
public export update, or further engineering route.
