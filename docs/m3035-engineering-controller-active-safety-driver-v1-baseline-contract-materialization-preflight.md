# M3035 Active Safety Driver v1 Baseline Contract Materialization Preflight

## Summary

- status: completed
- decision: `active_safety_driver_v1_baseline_contract_materialized_route_to_m3036_result_audit`
- baseline candidates: 2
- benchmark role rows: 17
- benchmark role nonzero rows: 17
- metric contract rows: 31
- metric rows available now: 25
- metric rows requiring future instrumentation: 6
- exclusion rule rows: 11
- actor contract guard pass: True
- claim boundary pass: True
- gate matrix pass: True
- required artifacts present: True
- follow-up manifest: `experiments/manifests/m3036-engineering-controller-active-safety-driver-v1-baseline-contract-materialization-result-audit.json`

## Input Denominator

- M3015 episode rows: 32
- M3015 profile aggregate rows: 2
- M3015 diagnostic success/collision/offtrack/speed-floor rows: 3 / 5 / 23 / 2
- M3018 localization rows: 32
- M3022 objective family rows: 4
- M3032 target tensor rows: 29
- M3032 zero-target success guards: 3

## Interpretation

M3035 materializes the Active Safety Driver v1 baseline contract. The two frozen checkpoint rows are candidate inputs for a later same-case baseline measurement, not ranked results. The benchmark role and metric rows define what the next runner must measure. The exclusion and claim-boundary rows prevent diagnostic rows, target tensors, self-ID proof rows, paper-only rows, or high-fidelity-unmapped rows from being used as driver-performance evidence.

Rejected claims:

```text
driver performance, validation result, current-sim verdict, high-fidelity validation readiness or result, repair success, checkpoint ranking, winner selection, checkpoint promotion, target tensor quality, residual fitting readiness, paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification
```

## Boundary

M3035 does not reset, step, roll out, train, validate, rank, promote, mutate checkpoints, run high-fidelity simulation, compare finite-window versus GRU, or claim driver performance.

## Next

- next blocker: `m3036-engineering-controller-active-safety-driver-v1-baseline-contract-materialization-result-audit`
- selected next action: `m3036-engineering-controller-active-safety-driver-v1-baseline-contract-materialization-result-audit`
