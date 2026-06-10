# M3115 Residual Failure Step/Action Influence Trace Materialization Preflight

## Summary

- status: completed
- result class: `active_safety_driver_residual_failure_step_action_influence_trace_materialization_pass`
- residual trace plan rows: 7/7
- residual step trace rows: 256
- residual action influence rows: 7
- residual trace failure rows: 0
- terminal collisions: 5
- terminal offtracks: 2
- max obstacle urgency: 0.7579162245811707
- max edge urgency: 0.9952551261521876
- gate matrix pass: True

## Diagnostic Labels

- collision_action_present_but_clearance_unresolved: 5
- offtrack_stability_recovery_limited: 2

## Interpretation

M3115 replays only the seven M3112 residual collision/offtrack rows through the already materialized M3110 direct-action function and records per-step actor-visible risk signals with direct [steer, throttle, brake] actions. These artifacts diagnose action influence only. They are not repair materialization, validation, ranking, promotion, repair-success, robustness-result, driver-performance, current-sim verdict, high-fidelity, paper, finite-window-vs-GRU, full-driver, or self-ID evidence.

Rejected claims:

```text
repair materialization, validation result, driver-performance verdict, current-sim verdict, robustness-result, repair success, checkpoint ranking, winner selection, checkpoint promotion, high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification
```

## Next

- next blocker: `m3116-engineering-controller-active-safety-driver-residual-failure-step-action-influence-trace-materialization-result-audit`
- follow-up manifest: `experiments/manifests/m3116-engineering-controller-active-safety-driver-residual-failure-step-action-influence-trace-materialization-result-audit.json`
