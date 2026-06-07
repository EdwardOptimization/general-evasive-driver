# M3000 Engineering Controller Route A Nonzero Residual Bounded Diagnostic Validation Preflight

## Summary

- status pass: `True`
- gate matrix pass: `True`
- required artifacts present: `True`
- candidate denominator rows: `43`
- candidate execution rows: `43`
- success-retention denominator rows: `13`
- success-retention execution rows: `13`
- failure rows: `0`
- stale exclusions protected: `11`
- parent comparison rows: `56`
- residual abs max: `0.0016821095487102866`
- diagnostic termination counts: `{'': 13, 'obstacle_collision': 7, 'off_track': 35, 'speed_too_low': 1}`
- next blocker: `m3001-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-bounded-diagnostic-validation-result-audit`
- follow-up manifest: `experiments/manifests/m3001-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-bounded-diagnostic-validation-result-audit.json`

## Boundary

M3000 records bounded closed-loop diagnostic fields only. Parent comparison remains report-only; stale fixed-source rows remain excluded from validation, paper, and self-ID denominators.

Rejected claims:

```text
ranking, winner selection, checkpoint promotion, success-rate verdict, validation result, repair success, driver performance, paper evidence, current-sim verdict, high-fidelity validation result, full ideal driver completion, finite-window-vs-GRU result, or level3 self-identification
```
