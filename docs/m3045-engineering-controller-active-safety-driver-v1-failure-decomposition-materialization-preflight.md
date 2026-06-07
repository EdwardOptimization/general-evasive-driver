# M3045 Active Safety Driver v1 Failure Decomposition Materialization Preflight

## Summary

- status: completed
- result class: `active_safety_driver_v1_failure_decomposition_materialization_preflight_pass`
- measurement rows preserved: 32/32
- failure mode rows: 17
- actuation saturation rows: 9
- repair requirement rows: 6
- success count: 4
- collision count: 4
- offtrack count: 24
- speed-too-low count: 1
- candidate action clip mean: 0.41243192505631066
- parent action clip mean: 0.0
- gate matrix pass: True

## Interpretation

M3045 materializes repair-facing failure and actuation decomposition artifacts from the accepted M3043 measurement rows. These artifacts are repair inputs for M3046 audit only. They are not validation, ranking, promotion, driver-performance, high-fidelity, paper, finite-window-vs-GRU, full-driver, or self-ID evidence.

Primary repair pressure:

```text
offtrack recovery: 24/32 rows
candidate action saturation: candidate action_clip_fraction_mean 0.41243192505631066
collision guard: 4/16 T5 rows collided
success preservation: all 4 success rows are parent-binding rows
speed-floor guard: 1 speed_too_low row
```

Rejected claims:

```text
validation result, driver-performance verdict, current-sim verdict, repair success, checkpoint ranking, winner selection, checkpoint promotion, high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification
```

## Next

- next blocker: `m3046-engineering-controller-active-safety-driver-v1-failure-decomposition-result-audit`
- follow-up manifest: `experiments/manifests/m3046-engineering-controller-active-safety-driver-v1-failure-decomposition-result-audit.json`
