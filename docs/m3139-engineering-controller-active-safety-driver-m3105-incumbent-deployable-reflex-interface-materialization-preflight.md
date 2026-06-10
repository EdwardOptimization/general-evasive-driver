# M3139 M3105-Incumbent Deployable Reflex Interface Materialization Preflight

## Summary

- status: completed
- result class: `active_safety_driver_m3105_incumbent_deployable_reflex_interface_materialization_pass`
- driver id: `active_safety_reflex_driver_m3105_incumbent_v4_no_regression`
- incumbent policy id: `m3103_v4_v2_fallback_no_regression_hard_safety_direct_action_repair`
- incumbent measurement: `m3105-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-full-fresh-measurement-preflight`
- action probe rows: 5
- residual blocker rows: 7
- M3105 success/collision/offtrack/speed-too-low: 57/5/2/0
- gate matrix pass: True

## Interpretation

M3139 binds the public `autodrift.active_safety_reflex_driver` runtime API to the current M3105/M3103 no-regression direct-action incumbent. The runtime remains actor-visible obs72 input to direct `[steer, throttle, brake]` output with no runtime base policy, checkpoint model, recurrent hidden state, hidden oracle input, target/source/route/outcome labels, TTC shortcut, validation, ranking, or promotion dependency.

This is a deployable interface artifact, not a repair-success or final-driver verdict. The M3105 residual blockers remain explicit: 5 collision rows and 2 offtrack rows on the 64-row fresh current-sim denominator.

Rejected claims:

```text
validation result, driver-performance verdict, current-sim verdict, robustness-result, repair success, checkpoint ranking, winner selection, checkpoint promotion, high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, feasibility proof, or level3 self-identification
```

## Next

- next blocker: `m3140-engineering-controller-active-safety-driver-m3105-incumbent-deployable-reflex-interface-result-audit`
- follow-up manifest: `experiments/manifests/m3140-engineering-controller-active-safety-driver-m3105-incumbent-deployable-reflex-interface-result-audit.json`
