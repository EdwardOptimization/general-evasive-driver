# M3147 Speed-Envelope Action-Delta Coverage Diagnostic Materialization Preflight

## Summary

- status: completed
- result class: `active_safety_driver_speed_envelope_action_delta_coverage_diagnostic_materialization_pass`
- residual action-delta plan rows: 7/7
- action-delta step trace rows: 256
- action-delta coverage rows: 7
- action-delta trace failure rows: 0
- overlay-any episode count: 7
- overlay-never episode count: 0
- zero-delta episode count: 0
- max overlay alpha: 0.7935389639658202
- max delta abs: 0.44438183307647705
- mean overlay active fraction: 0.9784557547715442
- gate matrix pass: True

## Diagnostic Labels

- candidate_action_saturation_may_limit_delta_effect: 2
- collision_terminal_window_delta_low: 1
- delta_present_outcome_unresolved: 4

## Interpretation

M3147 replays only the seven M3144 residual collision/offtrack rows through the M3142 direct-action candidate and records same-observation deltas against the M3105/M3103 fallback action. These artifacts diagnose overlay coverage, action saturation, and candidate-vs-fallback delta timing only. They are not a new repair implementation, validation, ranking, promotion, repair-success, robustness-result, driver-performance, current-sim verdict, high-fidelity, paper, finite-window-vs-GRU, full-driver, feasibility-proof, or self-ID evidence.

Rejected claims:

```text
repair implementation, validation result, driver-performance verdict, current-sim verdict, robustness-result, repair success, feasibility proof, checkpoint ranking, winner selection, checkpoint promotion, high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification
```

## Next

- next blocker: `m3148-engineering-controller-active-safety-driver-residual-trajectory-timing-speed-envelope-action-delta-coverage-diagnostic-result-audit`
- follow-up manifest: `experiments/manifests/m3148-engineering-controller-active-safety-driver-residual-trajectory-timing-speed-envelope-action-delta-coverage-diagnostic-result-audit.json`
