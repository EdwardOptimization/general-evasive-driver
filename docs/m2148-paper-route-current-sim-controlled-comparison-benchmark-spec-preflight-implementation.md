# M2148 Paper-Route Current-Sim Controlled Comparison Benchmark Spec Preflight Implementation

- status: completed
- decision: `current_sim_controlled_comparison_benchmark_spec_preflight_pass_route_to_audit`
- manifest: `experiments/manifests/m2148-paper-route-current-sim-controlled-comparison-benchmark-spec-preflight-implementation.json`
- implementation: `src/autodrift/paper_route_current_sim_controlled_comparison_benchmark_spec_preflight.py`
- tests: `tests/test_paper_route_current_sim_controlled_comparison_benchmark_spec_preflight.py`
- config artifact: `configs/paper_route_current_sim_controlled_comparison_benchmark_v0.json`
- run artifact: `runs/m2148_paper_route_current_sim_controlled_comparison_benchmark_spec_preflight/summary.json`
- reset/rollout/measured execution in M2148: `false`
- policy actions executed in M2148: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_controlled_comparison_benchmark_spec_preflight \
  --config-output configs/paper_route_current_sim_controlled_comparison_benchmark_v0.json \
  --output-dir runs/m2148_paper_route_current_sim_controlled_comparison_benchmark_spec_preflight \
  --next-blocker m2149-paper-route-current-sim-controlled-comparison-benchmark-spec-preflight-audit
```

## Result

```text
result_class: current_sim_controlled_comparison_benchmark_spec_preflight_pass
profile_count: 8
expected_profile_count: 8
missing_profile_count: 0
extra_profile_count: 0
task_family_count: 5
metric_count: 18
unsupported_metric_gap_count: 10
claim_boundary_row_count: 6
forbidden_profile_violation_count: 0
profile_specific_tuning_count: 0
guardrail_violation_count: 0
```

No reset, rollout, policy action, measured execution, training, replay, PPO,
checkpoint promotion, profile tuning, ranking, paper claim, finite-window vs GRU
verdict, or level3 self-ID claim is made.

## Profile Matrix

M2148 materializes the planned 8-profile matrix:

```text
L0_current_masked
L1_one_step
L2_window_13
L2_window_25
L2_window_50
L2_window_100
L3_online_gru
L3_reset_control
```

All profiles preserve:

```text
input_contract: P0_human_view_no_wheel_no_oracle
action_contract: steer_throttle_brake
forbidden_actor_input_violation: false
profile_specific_tuning: false
```

The reset-control field is only true for the recurrent reset-control profile:

```text
L3_reset_control: reset_or_truncated_control=true
L2 finite-window profiles: reset_or_truncated_control=false
```

This avoids confusing finite-window per-decision history with recurrent hidden
reset/truncation controls.

## Task Families

M2148 materializes the five paper-route task families as benchmark candidates:

```text
T1_reactive_emergency_avoidance
T2_delayed_actuator_response
T3_diagnostic_warmup_obstacle_reveal
T4_same_current_different_older_history
T5_terminal_boundary_near_constraint
```

Each task row is marked:

```text
paper_validity_status: current_sim_benchmark_candidate_not_executed
generated_proxy_source: false
reset_validation_required: true
measured_execution_required: true
```

Therefore the artifact is a benchmark contract, not measured paper evidence.

## Metric Support

Supported after measured audit:

```text
success_rate
collision_rate
road_departure_rate
clearance_margin_tail
recovery_after_maneuver
control_smoothness
source_diversity
max_single_source_share
```

Explicit deferred gaps:

```text
spin_rate
terminal_margin_tail
first_critical_action_gap
short_horizon_maneuver_gap
future_braking_authority_prediction
future_yaw_authority_prediction
adaptation_latency
wrong_history_margin_gap
delayed_history_margin_gap
reset_or_truncated_history_margin_gap
```

These are deliberately not approximated. They must be repaired, instrumented, or
kept out of claims before paper-level comparison.

## Claim Boundary

Admissible:

```text
current_sim_controlled_comparison_benchmark_spec_preflight_completed
```

Blocked:

```text
controller_family_ranking
winner_selection
finite_window_vs_gru_conclusion
paper_level_benchmark_result
level3_self_identification
```

## Next

Immediate next milestone:

```text
m2149-paper-route-current-sim-controlled-comparison-benchmark-spec-preflight-audit
```

M2149 should audit the benchmark contract before any reset validation command
design. The likely next route is reset-validation command design if M2149
accepts the explicit metric gaps as bounded and non-silent.
