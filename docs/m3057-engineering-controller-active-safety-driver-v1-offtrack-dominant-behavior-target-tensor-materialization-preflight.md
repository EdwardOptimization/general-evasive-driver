# M3057 Active Safety Driver v1 Offtrack-Dominant Behavior Target Tensor Materialization Preflight

## Summary

- status: fail_closed
- result class: `active_safety_driver_v1_offtrack_behavior_target_tensor_materialization_fail_closed_missing_raw_actor_view_traces`
- decision: `active_safety_driver_v1_offtrack_behavior_target_tensor_materialization_fail_closed_route_to_m3058_result_audit`
- next blocker: `m3058-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-target-tensor-materialization-result-audit`
- follow-up manifest: `experiments/manifests/m3058-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-target-tensor-materialization-result-audit.json`

M3057 attempted to convert the M3056-accepted M3055 fitting contract and M3053
behavior target-source rows into trainer-side numeric target tensors. It fails
closed because the available M3053/M3055 artifacts contain episode-level
behavior rows but no raw actor-view observation/action traces. M3057 therefore
writes blocker rows and guard artifacts rather than fabricating target tensors.

## Artifact Summary

```text
behavior target tensor blocker rows: 24
raw actor-view traces required: 24
raw actor-view traces available: 0
raw actor-view traces missing: 24
numeric target tensors materialized: 0
target tensor weight spec rows: 6
actor-contract guard rows: 10
target-visibility guard rows: 7
side-effect guard rows: 16
claim-boundary rows: 14
gate rows: 26
```

## Supported Claims

M3057 supports only these bounded claims:

```text
target tensor materialization was attempted under the accepted fitting contract
24 offtrack behavior target-source rows were preserved as blocker rows
raw actor-view traces are required and currently absent for numeric target tensor materialization
actor observation 72 and action 3 direct [steer, throttle, brake] contract is preserved
target labels and provenance remain outside actor inputs
M3058 result-audit manifest was registered
```

## Rejected Claims

M3057 rejects:

```text
numeric target tensor quality
fitting execution
fitted policy quality
repair success
driver performance
validation ranking promotion current-sim high-fidelity paper finite-window-vs-GRU full-driver or self-ID evidence
```

## Boundary

M3057 is fail-closed target tensor materialization only. It writes no fitted
weights and runs no environment interaction, local action search, fitting,
training, validation, ranking, promotion, high-fidelity simulation,
finite-window-vs-GRU comparison, paper evaluation, full-driver evaluation, or
self-ID testing.
