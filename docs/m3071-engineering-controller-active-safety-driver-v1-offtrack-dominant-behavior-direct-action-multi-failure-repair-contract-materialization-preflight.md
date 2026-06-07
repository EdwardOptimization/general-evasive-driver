# M3071 Active Safety Driver v1 Direct-Action Multi-Failure Repair Contract Materialization Preflight

## Summary

- status: completed
- result class: `active_safety_driver_v1_direct_action_multi_failure_repair_contract_materialization_preflight_pass`
- measurement rows preserved: 32/32
- repair contract rows: 1
- loss family rows: 6
- row admission rows: 32
- guard family rows: 9
- requirement families preserved: 7
- success/collision/offtrack/speed-too-low: 8 / 4 / 16 / 5
- gate matrix pass: True

## Interpretation

M3071 materializes one fit-ready direct-action repair contract from M3070/M3069 evidence. The contract is a trainer-side artifact for M3072 audit only. It is not target quality, fitted policy quality, validation, ranking, promotion, repair-success, driver-performance, high-fidelity, paper, finite-window-vs-GRU, full-driver, or self-ID evidence.

Contract gates:

```text
p0 offtrack containment and recovery
p0 T5 collision guard
p1 speed-floor recovery
p1 direct-action raw/final action pressure
p1 success preservation
p1 stability and clearance tradeoff
p0 actor contract and claim boundary
```

Rejected claims:

```text
target quality, fitted policy quality, validation result, driver-performance verdict, current-sim verdict, repair success, checkpoint ranking, winner selection, checkpoint promotion, high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification
```

## Next

- next blocker: `m3072-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-multi-failure-repair-contract-result-audit`
- follow-up manifest: `experiments/manifests/m3072-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-multi-failure-repair-contract-result-audit.json`
