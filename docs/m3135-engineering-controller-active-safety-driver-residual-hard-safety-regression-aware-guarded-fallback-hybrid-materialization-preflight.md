# M3135 Regression-Aware Guarded Fallback Hybrid Materialization Preflight

## Summary

- status: completed
- result class: `active_safety_driver_residual_hard_safety_regression_aware_guarded_fallback_hybrid_materialization_pass`
- rule rows: 9
- runtime contract rows: 5
- actor-input exclusion rows: 12
- action probe rows: 5
- fallback probe rows: 4
- bounded mix probe rows: 1
- gate matrix pass: True

## Interpretation

M3135 materializes a callable actor-visible obs72-to-action3 guarded fallback hybrid. It defaults to the M3105/M3103 no-regression direct-action path and only admits bounded corridor-style adjustment when actor-visible guards permit it. It does not run the environment or make repair-success claims.

Rejected claims:

```text
measurement result, validation result, driver-performance verdict, current-sim verdict, robustness-result, repair success, feasibility proof, checkpoint ranking, winner selection, checkpoint promotion, high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification
```

## Next

- next blocker: `m3136-engineering-controller-active-safety-driver-residual-hard-safety-regression-aware-guarded-fallback-hybrid-materialization-result-audit`
- follow-up manifest: `experiments/manifests/m3136-engineering-controller-active-safety-driver-residual-hard-safety-regression-aware-guarded-fallback-hybrid-materialization-result-audit.json`
