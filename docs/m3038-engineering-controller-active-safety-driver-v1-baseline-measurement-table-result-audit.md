# M3038 Active Safety Driver v1 Baseline Measurement Table Result Audit

## Summary

- status: completed
- decision: `accept_m3037_baseline_measurement_table_route_to_m3039_guarded_training_admission_materialization`
- audited milestone: `m3037-engineering-controller-active-safety-driver-v1-baseline-measurement-table-materialization-preflight`
- next route: `m3039-engineering-controller-active-safety-driver-v1-guarded-training-admission-materialization-preflight`

M3038 accepts M3037 as a complete and claim-safe baseline measurement table
materialization. It does not accept the table as a validation result, driver
performance verdict, checkpoint ranking, winner selection, promotion decision,
paper result, high-fidelity readiness claim, finite-window-vs-GRU claim, full
driver completion claim, or self-ID claim.

## Artifact Audit

Accepted M3037 facts:

```text
status_pass: true
gate_matrix_pass: true
baseline_measurement_rows: 32
candidate_profile_metric_aggregate_rows: 2
benchmark_role_metric_aggregate_rows: 34
metric_coverage_rows: 31
required_metric_coverage: 25/25
actor_contract_guard_rows_pass: true
claim_boundary_rows_pass: true
actor contract: 72/action 3
environment reset/step/rollout/training/validation/ranking/promotion: false
driver-performance/current-sim/high-fidelity/paper/self-ID claims: false
```

Required artifacts were present:

```text
runs/m3037_engineering_controller_active_safety_driver_v1_baseline_measurement_table_materialization_preflight/summary.json
runs/m3037_engineering_controller_active_safety_driver_v1_baseline_measurement_table_materialization_preflight/baseline_measurement_rows.csv
runs/m3037_engineering_controller_active_safety_driver_v1_baseline_measurement_table_materialization_preflight/candidate_profile_metric_aggregate_rows.csv
runs/m3037_engineering_controller_active_safety_driver_v1_baseline_measurement_table_materialization_preflight/benchmark_role_metric_aggregate_rows.csv
runs/m3037_engineering_controller_active_safety_driver_v1_baseline_measurement_table_materialization_preflight/metric_coverage_rows.csv
runs/m3037_engineering_controller_active_safety_driver_v1_baseline_measurement_table_materialization_preflight/actor_contract_guard_rows.csv
runs/m3037_engineering_controller_active_safety_driver_v1_baseline_measurement_table_materialization_preflight/claim_boundary_rows.csv
runs/m3037_engineering_controller_active_safety_driver_v1_baseline_measurement_table_materialization_preflight/gate_matrix.csv
docs/m3037-engineering-controller-active-safety-driver-v1-baseline-measurement-table-materialization-preflight.md
experiments/manifests/m3038-engineering-controller-active-safety-driver-v1-baseline-measurement-table-result-audit.json
```

## Baseline Pressure

The materialized same-case baseline pressure is negative and useful for
engineering admission, but it is not a ranking or validation verdict.

```text
route_a_candidate_m2655_mitigation_preserving:
  rows: 16
  success: 0
  collision: 2
  off_track_termination: 13
  speed_too_low_termination: 2
  min_clearance_margin_min: -0.24160113106273284
  high_sideslip_fraction_mean: 0.5598900710403859

route_a_parent_l3_online_gru:
  rows: 16
  success: 3
  collision: 3
  off_track_termination: 10
  speed_too_low_termination: 0
  min_clearance_margin_min: -0.1490127007932378
  high_sideslip_fraction_mean: 0.03365384615384615
```

These numbers identify the initial safety failure pressure for Active Safety
Driver v1. They support moving to guarded engineering-training admission. They
do not select the parent over the candidate or promote either checkpoint.

## Rejected Claims

M3038 explicitly rejects:

```text
driver-performance verdict
validation result
current-sim verdict
high-fidelity validation readiness or result
checkpoint ranking
winner selection
checkpoint promotion
repair success
paper evidence
finite-window-vs-GRU conclusion
full ideal driver completion
level3 self-identification
```

M3037 used M3032 target tensors only as offline context. M3038 preserves that
boundary: target tensors may inform trainer-side objective admission later, but
they are not closed-loop performance evidence and must never be actor-visible.

## Route Decision

M3038 selects exactly one next route:

```text
m3039-engineering-controller-active-safety-driver-v1-guarded-training-admission-materialization-preflight
```

Rationale:

```text
1. Phase A baseline measurement is now machine-readable and audited.
2. The baseline failure pressure is strong enough to justify Phase B engineering-training admission.
3. The next route must keep actor 72/action 3 and block hidden/oracle/TTC/target/verdict actor inputs.
4. The next route should materialize active-safety training objectives, scenario roles, guardrails, and admission gates before any fitting or PPO run.
5. Self-ID, GRU, finite-window, and paper evidence stay auxiliary and cannot define the mainline objective.
```

## Boundary

M3038 does not run reset, step, rollout, replay, PPO, fitting, training,
validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU
comparison, or self-ID testing. It only audits M3037 and registers M3039.
