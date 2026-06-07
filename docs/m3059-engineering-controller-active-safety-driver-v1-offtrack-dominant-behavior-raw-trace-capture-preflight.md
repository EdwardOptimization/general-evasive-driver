# M3059 Active Safety Driver v1 Offtrack-Dominant Behavior Raw Trace Capture Preflight

## Summary

- status: pass
- result class: `active_safety_driver_v1_offtrack_behavior_raw_trace_capture_preflight_pass`
- decision: `active_safety_driver_v1_offtrack_behavior_raw_trace_capture_route_to_m3060_result_audit`
- next blocker: `m3060-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-raw-trace-capture-result-audit`
- follow-up manifest: `experiments/manifests/m3060-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-raw-trace-capture-result-audit.json`

M3059 reruns the M3057 offtrack target tensor blocker denominator only to
persist raw actor-view observation/action/next-observation/reward/done/timeout
traces. The replay uses the same M3050 executable workload lineage and the same
M3048 action-headroom-constrained residual adapter recorded by M3050.

## Artifact Summary

```text
capture plan rows: 24
capture plan rows passing precheck: 24
raw trace index rows: 24
raw traces persisted: 24
raw traces missing: 0
raw trace availability rows: 24
raw trace guard rows: 24
total captured steps: 2692
trace step counts match M3050: True
actor-contract guard rows: 20
claim-boundary rows: 17
gate rows: 23
```

## Supported Claims

M3059 supports only these bounded claims:

```text
raw actor-view trace capture was attempted for the 24 M3057 blocker rows
persisted trace files contain observation/action/next-observation/reward/done/timeout arrays
actor observation 72 and action 3 direct [steer, throttle, brake] contract is preserved
target labels, target provenance, source labels, route labels, outcome labels, progress labels, verdict labels, TTC, and oracle values remain outside actor inputs
M3060 result-audit manifest was registered
```

## Rejected Claims

M3059 rejects:

```text
numeric target tensor quality
target tensor materialization
fitting execution
fitted policy quality
repair success
driver performance
validation ranking promotion current-sim high-fidelity paper finite-window-vs-GRU full-driver or self-ID evidence
```

## Boundary

M3059 is raw trace capture only. It writes no target tensors, fitted weights, or
policy checkpoints and runs no local-action search, fitting, training,
validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU
comparison, paper evaluation, full-driver evaluation, or self-ID testing.
