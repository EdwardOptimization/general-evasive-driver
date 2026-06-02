# M2363 Paper-Route Current-Sim Dual-Axis Repaired Pack Measured Execution Result Audit

- status: completed
- decision: `measured_execution_result_accepted_route_to_outcome_localization_design`
- manifest: `experiments/manifests/m2363-paper-route-current-sim-dual-axis-repaired-pack-measured-execution-result-audit.json`
- audited summary: `runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/summary.json`
- reset/rollout rerun in M2363: `false`
- policy action executed in M2363: `false`
- training/replay/PPO: `false`
- support-policy ranking claim made: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Artifact Audit

M2363 accepts M2362 as a complete measured-execution artifact:

```text
result_class: current_sim_dual_axis_repaired_pack_measured_execution_pass
episode_count: 5400
config_pack_count: 5
scenario_specs_per_pack_count: 72
pack_aware_scenario_spec_count: 360
selected_checkpoint_count: 15
failure_count: 0
validation_failure_count: 0
metadata_missing_count: 0
metric_completeness_failure_count: 0
guardrail_violation_count: 0
```

This is a valid closed-loop outcome artifact. It is not a ranking, promotion,
paper verdict, finite-window-vs-GRU conclusion, or self-ID mechanism result.

## Global Outcome

Global outcome is weak and offtrack-dominated:

```text
success_rate: 0.06518518518518518
collision_rate: 0.19962962962962963
offtrack_rate: 0.7262962962962963
max_step_noncompletion_rate: 0.005925925925925926
other_failure_rate: 0.002962962962962963
dominant_failure_mode: offtrack_dominated_failure
mean_min_clearance_margin: 6.79116992686492
min_min_clearance_margin: -0.3747987476447765
```

## Slice Audit

Pack-level spread is small, so M2363 does not select a winner pack:

```text
baseline_reference_pack success/offtrack: 0.0657 / 0.7204
g_primary_pack success/offtrack: 0.0630 / 0.7250
h_primary_pack success/offtrack: 0.0667 / 0.7296
g_h_primary_pack success/offtrack: 0.0657 / 0.7296
gh_minimal_pack success/offtrack: 0.0648 / 0.7269
```

Profile-level aggregates are diagnostic only:

```text
L0_current_masked success/offtrack/collision: 0.0556 / 0.7704 / 0.1676
L1_one_step success/offtrack/collision: 0.0556 / 0.7796 / 0.1639
L2_window_25 success/offtrack/collision: 0.0556 / 0.7204 / 0.2185
L2_window_50 success/offtrack/collision: 0.0556 / 0.7139 / 0.2250
L3_online_gru success/offtrack/collision: 0.1037 / 0.6472 / 0.2231
```

This is not a finite-window-vs-GRU conclusion because the measured artifact was
not designed as a verdict protocol and has not been audited for role-specific
tradeoffs or statistical significance.

Role-level outcome localizes the dominant issue:

```text
R0_stable_avoidable success/offtrack/collision: 0.0611 / 0.9344 / 0.0011
R1_aeb_infeasible_stable_aes success/offtrack/collision: 0.3300 / 0.6656 / 0.0044
R2_handling_limit_drift_capable_avoidance success/offtrack/collision: 0.0000 / 0.8289 / 0.1600
R3_recovery_after_limit success/offtrack/collision: 0.0000 / 0.8389 / 0.1467
R4_unavoidable_mitigation success/offtrack/collision: 0.0000 / 0.2611 / 0.7389
R5_hidden_dynamics_robustness success/offtrack/collision: 0.0000 / 0.8289 / 0.1467
```

Primary offtrack target slices include:

```text
R0 all packs: offtrack about 0.933-0.939
profile x R0 for L0/L1/L2: offtrack 1.0
R2/R3/R5: zero success and high offtrack
R5 nominal_neighbor and weak_brake: offtrack 0.9889 and 0.9556
early_far timing: offtrack 0.8778
```

R4 is a separate collision-dominated mitigation semantics slice and should not
be mixed with offtrack repair targets.

## Decision

M2363 accepts M2362 and routes to artifact-only outcome localization design.

The next route should:

```text
localize offtrack target slices;
separate collision-dominated R4 mitigation slices;
separate pack/profile/role/hidden/timing/lateral axes;
preserve denominator and no-ranking claim boundary;
avoid training or rerun until localization is audited.
```

Next:

```text
m2364-paper-route-current-sim-dual-axis-measured-outcome-localization-design
```
