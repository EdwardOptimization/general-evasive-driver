# M3055 Active Safety Driver v1 Offtrack-Dominant Behavior Fitting Contract Materialization Preflight

## Summary

- status: completed
- decision: `active_safety_driver_v1_offtrack_behavior_fitting_contract_materialized_route_to_m3056_result_audit`
- next blocker: `m3056-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-fitting-contract-materialization-result-audit`
- follow-up manifest: `experiments/manifests/m3056-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-fitting-contract-materialization-result-audit.json`

M3055 materializes the fitting contract for a later deployable offtrack-
dominant behavior recovery selector/reflex. The runtime contract is direct
`obs72 -> [steer, throttle, brake]`, without a base-policy dependency and
without hidden/oracle/TTC/target/provenance/source/route/outcome/progress/
verdict actor inputs.

## Contract Summary

```text
observation_shape: 72
action_shape: 3
output_semantics: direct_action
output_components: steer / throttle / brake
base_policy_required_at_runtime: False
fitting_contract_rows: 1
loss_family_rows: 6
row_admission_rows: 5
actor_contract_guard_rows: 9
target_visibility_guard_rows: 5
side_effect_guard_rows: 16
gate_rows: 18
```

## Source Counts

```text
M3053 offtrack target-source rows: 24
M3053 candidate blocker rows: 16
M3053 collision guard rows: 4
M3053 success-preservation guard rows: 4
M3053 speed-floor guard rows: 1
```

## Supported Claims

M3055 supports only these bounded claims:

```text
one behavior fitting contract was materialized
direct action output [steer, throttle, brake] was specified
offtrack recovery collision guard success preservation speed floor stability and smoothness loss families are separated
actor-contract target-visibility side-effect and claim-boundary guards pass
M3056 result-audit manifest was registered
```

## Rejected Claims

M3055 rejects:

```text
target tensor quality
fitting execution
fitted policy quality
repair success
driver performance
validation ranking promotion current-sim high-fidelity paper finite-window-vs-GRU full-driver or self-ID evidence
```

## Boundary

M3055 is fitting-contract materialization only. It writes no fitted weights and
runs no environment interaction.
