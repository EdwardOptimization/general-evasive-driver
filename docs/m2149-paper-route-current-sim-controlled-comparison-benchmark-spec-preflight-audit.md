# M2149 Paper-Route Current-Sim Controlled Comparison Benchmark Spec Preflight Audit

- status: completed
- decision: `current_sim_benchmark_spec_preflight_audit_route_to_executable_spec_materialization_design`
- manifest: `experiments/manifests/m2149-paper-route-current-sim-controlled-comparison-benchmark-spec-preflight-audit.json`
- audited summary: `runs/m2148_paper_route_current_sim_controlled_comparison_benchmark_spec_preflight/summary.json`
- reset/rollout/measured execution in M2149: `false`
- policy actions executed in M2149: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Audit Result

M2148 is a clean no-rollout benchmark contract preflight:

```text
result_class: current_sim_controlled_comparison_benchmark_spec_preflight_pass
profile_count: 8 / 8
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

The profile matrix is complete for the first current-sim benchmark pack:

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

The task-family coverage is complete for the design contract:

```text
T1_reactive_emergency_avoidance
T2_delayed_actuator_response
T3_diagnostic_warmup_obstacle_reveal
T4_same_current_different_older_history
T5_terminal_boundary_near_constraint
```

## Metric Gap Audit

M2148 has `10` explicit deferred metric gaps:

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

These gaps are acceptable for a benchmark contract preflight because they are
explicit and non-silent. They are not acceptable for paper-level mechanism
claims until instrumentation, intervention execution, or narrower claim
boundaries repair them.

## Claim Boundary Audit

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

The artifact is therefore safe as a benchmark contract. It is not performance
evidence.

## Route Correction

The M2149 manifest originally allowed reset-validation command design as the
happy path. The audit finds one missing intermediate layer:

```text
M2148 task rows are benchmark-family contract rows, not executable env specs.
```

They do not yet contain enough concrete current-simulator scenario parameters,
source IDs, seeds, or env-config deltas to reset validate directly. A direct
reset-validation command would either be impossible or would smuggle in an
implicit materialization step.

The correct next milestone is therefore:

```text
m2150-paper-route-current-sim-controlled-comparison-executable-spec-materialization-design
```

M2150 should design a no-rollout conversion from the M2148 benchmark contract
into executable current-sim scenario specs. Reset validation should remain
blocked until those executable specs exist and are audited.

## Supported and Unsupported Claims

Supported:

```text
M2148 produced a clean no-rollout benchmark contract artifact with complete
profile matrix, T1-T5 task-family coverage, explicit metric gaps, and guardrail 0.
```

Unsupported:

```text
reset-valid scenario specs exist;
measured execution can start;
controller-family ranking;
finite-window-vs-GRU verdict;
paper-level benchmark result;
level3 self-identification.
```

## Next

Immediate next milestone:

```text
m2150-paper-route-current-sim-controlled-comparison-executable-spec-materialization-design
```
