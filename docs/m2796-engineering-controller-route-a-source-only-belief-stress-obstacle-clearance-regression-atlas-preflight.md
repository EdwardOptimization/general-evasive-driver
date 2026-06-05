# M2796 Engineering Controller Route A Source-Only Belief-Stress Obstacle-Clearance Regression Atlas

## Metadata

- status: completed
- result class: `engineering_controller_route_a_source_only_belief_stress_obstacle_clearance_regression_atlas_preflight_pass`
- manifest: `experiments/manifests/m2796-engineering-controller-route-a-source-only-belief-stress-obstacle-clearance-regression-atlas-preflight.json`
- summary: `runs/m2796_engineering_controller_route_a_source_only_belief_stress_obstacle_clearance_regression_atlas/summary.json`
- clearance regression rows: `runs/m2796_engineering_controller_route_a_source_only_belief_stress_obstacle_clearance_regression_atlas/clearance_regression_rows.csv`
- aggregate rows: `runs/m2796_engineering_controller_route_a_source_only_belief_stress_obstacle_clearance_regression_atlas/clearance_regression_aggregate_rows.csv`
- follow-up manifest: `experiments/manifests/m2797-engineering-controller-route-a-source-only-belief-stress-obstacle-clearance-regression-atlas-result-audit.json`
- next: `m2797-engineering-controller-route-a-source-only-belief-stress-obstacle-clearance-regression-atlas-result-audit`

## Evidence Summary

M2796 reanalyzed M2793 source/base/candidate triad deltas only. It did not
execute reset, step, policy action, rollout, replay, validation, training,
PPO, source build, adapter probe, or external simulation.

```text
m2793_triad_execution_rows: 216
candidate_minus_source_delta_rows: 72
candidate_minus_base_delta_rows: 72
clearance_regression_rows: 144
clearance_regression_aggregate_rows: 237
proof_gate_rows: 16
```

The hard obstacle-clearance guard remains mixed and skew negative:

```text
candidate_minus_source_positive: 30
candidate_minus_source_negative: 42
candidate_minus_source_mean_delta_m: -0.0003189920460919861
candidate_minus_source_median_delta_m: -0.0026030437199309198
candidate_minus_base_positive: 29
candidate_minus_base_negative: 43
candidate_minus_base_mean_delta_m: -0.00013214111660788612
candidate_minus_base_median_delta_m: -0.00039442807985579087
```

## Top Negative Aggregate Rows

- delta_family `delta_family=candidate_minus_base`: negative 43/72, rate 0.597222, mean -0.00013214111660788612
- delta_family `delta_family=candidate_minus_source`: negative 42/72, rate 0.583333, mean -0.0003189920460919861
- delta_family_seed_index `delta_family=candidate_minus_base|seed_index=11`: negative 12/18, rate 0.666667, mean -0.00020894025145860398
- delta_family_seed_index `delta_family=candidate_minus_base|seed_index=8`: negative 12/18, rate 0.666667, mean -0.0003612355662162435
- delta_family_seed_index `delta_family=candidate_minus_source|seed_index=10`: negative 12/18, rate 0.666667, mean -0.0005099305535785698
- delta_family_seed_index `delta_family=candidate_minus_source|seed_index=11`: negative 12/18, rate 0.666667, mean -0.0013793408484996045
- delta_family_seed_index `delta_family=candidate_minus_source|seed_index=8`: negative 12/18, rate 0.666667, mean -0.0017106252039252683
- delta_family_seed_index `delta_family=candidate_minus_base|seed_index=10`: negative 10/18, rate 0.555556, mean 2.602268759265157e-05
- delta_family_seed_index `delta_family=candidate_minus_base|seed_index=9`: negative 9/18, rate 0.500000, mean 1.558866365065143e-05
- delta_family_seed_index `delta_family=candidate_minus_source|seed_index=9`: negative 6/18, rate 0.333333, mean 0.002323928421635498
- delta_family_role_dynamics_stress `delta_family=candidate_minus_base|role_family=drift_required_recovery|dynamics_axis=fresh_fault_delay_noise|stress_family=held_actuator_history_stress`: negative 4/4, rate 1.000000, mean -0.0006200679637941575
- delta_family_role_dynamics_stress `delta_family=candidate_minus_base|role_family=drift_required_recovery|dynamics_axis=fresh_fault_delay_noise|stress_family=previous_command_history_stress`: negative 4/4, rate 1.000000, mean -0.0006330037940679434

## Claim Boundary

M2796 supports source-only clearance-regression attribution artifacts only.
It rejects validation, ranking, winner selection, checkpoint promotion,
success-rate verdict, repair success, driver performance, paper result,
current-sim verdict, high-fidelity validation, full-driver completion,
finite-window-vs-GRU conclusion, and self-ID interpretation.

## Next

Route to M2797 result audit before using the atlas to design a future
training, architecture, or controller change.
