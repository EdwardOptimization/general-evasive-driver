# M3037 Active Safety Driver v1 Baseline Measurement Table Materialization Preflight

## Summary

- status: completed
- decision: `active_safety_driver_v1_baseline_measurement_table_materialized_route_to_m3038_result_audit`
- baseline measurement rows: 32
- candidate profile aggregate rows: 2
- benchmark role aggregate rows: 34
- metric coverage rows: 31
- required metric coverage: 25/25
- actor contract guard pass: True
- claim boundary pass: True
- gate matrix pass: True
- follow-up manifest: `experiments/manifests/m3038-engineering-controller-active-safety-driver-v1-baseline-measurement-table-result-audit.json`

## Candidate Baseline Aggregates

### route_a_candidate_m2655_mitigation_preserving

- episode count: 16
- success/collision/off-track/speed-floor counts: 0 / 2 / 13 / 2
- success rate: 0.0
- collision rate: 0.125
- off-track termination rate: 0.8125
- min clearance margin mean/p10/p5/min: 7.304892735923677 / 0.7178456972093354 / -0.12472348109466291 / -0.24160113106273284
- high sideslip fraction mean/p95: 0.5598900710403859 / 0.7737900588620014
- action rate mean/p95: 0.01253065504715778 / 0.019777159206569195

### route_a_parent_l3_online_gru

- episode count: 16
- success/collision/off-track/speed-floor counts: 3 / 3 / 10 / 0
- success rate: 0.1875
- collision rate: 0.1875
- off-track termination rate: 0.625
- min clearance margin mean/p10/p5/min: 7.103823257262891 / -0.027379607311522114 / -0.0766354740101482 / -0.1490127007932378
- high sideslip fraction mean/p95: 0.03365384615384615 / 0.1346153846153846
- action rate mean/p95: 0.0016879059694474563 / 0.0030549801304005086

## Interpretation

M3037 materializes official Active Safety Driver v1 baseline measurement tables from already executed M3015 closed-loop rows under the accepted M3035 contract. These aggregates expose collision, off-track, clearance, stability, recovery, action-rate, and role-split baseline pressure. They do not rank the candidate and parent, select a winner, promote a checkpoint, or claim driver performance.

Rejected claims:

```text
checkpoint ranking, winner selection, checkpoint promotion, validation result, repair success, driver-performance verdict, current-sim verdict, paper evidence, high-fidelity validation readiness or result, finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification
```

## Boundary

M3037 does not reset, step, roll out, train, validate, rank, promote, mutate checkpoints, run high-fidelity simulation, compare finite-window versus GRU, or use M3032 target tensors as closed-loop evidence.

## Next

- next blocker: `m3038-engineering-controller-active-safety-driver-v1-baseline-measurement-table-result-audit`
- selected next action: `m3038-engineering-controller-active-safety-driver-v1-baseline-measurement-table-result-audit`
