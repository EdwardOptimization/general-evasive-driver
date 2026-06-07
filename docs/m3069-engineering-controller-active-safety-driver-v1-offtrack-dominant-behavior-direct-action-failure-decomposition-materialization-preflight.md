# M3069 Active Safety Driver v1 Direct-Action Failure Decomposition Materialization Preflight

## Summary

- status: completed
- result class: `active_safety_driver_v1_direct_action_failure_decomposition_materialization_preflight_pass`
- measurement rows preserved: 32/32
- direct-action failure mode rows: 31
- direct-action actuation pressure rows: 13
- direct-action recovery stability rows: 13
- direct-action repair requirement rows: 7
- success count: 8
- collision count: 4
- offtrack count: 16
- speed-too-low count: 5
- raw action abs max: 2.2606801986694336
- action clip fraction mean: 0.03451952273501378
- final action abs max: 1.0
- gate matrix pass: True

## Interpretation

M3069 materializes repair-facing direct-action failure, actuation, recovery, and stability decomposition artifacts from the accepted M3067 measurement rows. These artifacts are repair inputs for M3070 audit only. They are not validation, ranking, promotion, driver-performance, high-fidelity, paper, finite-window-vs-GRU, full-driver, repair-success, or self-ID evidence.

Primary repair pressure:

```text
offtrack recovery: 16/32 rows
T5 collision guard: 4 T5 collision rows
speed-floor recovery: 5 speed_too_low rows
direct-action clipping pressure: action_clip_fraction_mean 0.03451952273501378
raw action pressure: raw_action_abs_max 2.2606801986694336
```

Rejected claims:

```text
validation result, driver-performance verdict, current-sim verdict, repair success, checkpoint ranking, winner selection, checkpoint promotion, high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification
```

## Next

- next blocker: `m3070-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-failure-decomposition-result-audit`
- follow-up manifest: `experiments/manifests/m3070-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-failure-decomposition-result-audit.json`
