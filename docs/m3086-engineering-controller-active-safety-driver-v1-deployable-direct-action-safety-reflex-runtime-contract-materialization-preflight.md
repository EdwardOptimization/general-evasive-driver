# M3086 Active Safety Driver v1 Deployable Runtime Contract Materialization Preflight

## Summary

- status: completed
- result class: `active_safety_driver_v1_deployable_direct_action_safety_reflex_runtime_contract_materialization_preflight_pass`
- driver id: `active_safety_reflex_driver_v1_m3078_deterministic`
- policy config sha256: `4e3b185f2f98208b9700280174cf3b4401ae418207da8cb293c72b0c4427d40c`
- interface rows: 2
- action probe rows: 5
- actor-input exclusion rows: 10
- claim-boundary rows: 21
- gate matrix pass: True
- runtime base policy required: False
- checkpoint model required: False
- output: `action = ActiveSafetyReflexDriver.act(obs72) -> [steer, throttle, brake]`

## Interpretation

M3086 materializes a directly callable obs72-to-action3 [steer throttle brake] runtime contract for the deterministic safety-reflex layer. It is packaging and contract evidence only. It is not validation, ranking, promotion, repair-success, driver-performance, high-fidelity, paper, finite-window-vs-GRU, full-driver, robustness-result, or self-ID evidence.

Rejected claims:

```text
validation result, driver-performance verdict, current-sim verdict, robustness-result, repair success, checkpoint ranking, winner selection, checkpoint promotion, high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification
```

## Next

- next blocker: `m3087-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-runtime-contract-materialization-result-audit`
- follow-up manifest: `experiments/manifests/m3087-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-runtime-contract-materialization-result-audit.json`
