# M3150 Residual Action-Delta Effectiveness Counterfactual Sensitivity Diagnostic

## Summary

- status: completed
- result class: `active_safety_driver_residual_action_delta_sensitivity_diagnostic_materialization_pass`
- residual effectiveness rows: 7/7
- source M3147 step rows: 256
- headroom available rows: 5
- saturation-limited rows: 2
- terminal-delta-low rows: 1
- delta-present counterfactual-needed rows: 3
- gate matrix pass: True

## Sensitivity Labels

- collision_action_saturation_limited: 2
- collision_delta_present_counterfactual_needed: 2
- collision_terminal_delta_low_headroom_available: 1
- offtrack_delta_present_counterfactual_needed: 1
- offtrack_steer_delta_low_headroom_available: 1

## Interpretation

M3150 reanalyzes existing M3147 action-delta traces only. It estimates terminal-window action headroom, delta utilization, and saturation labels for the seven residual rows. These artifacts are diagnostic and no-new-execution. They are not repair implementation, validation, ranking, promotion, repair-success, robustness-result, driver-performance, current-sim verdict, high-fidelity, paper, finite-window-vs-GRU, full-driver, feasibility-proof, or self-ID evidence.

Rejected claims:

```text
repair implementation, validation result, driver-performance verdict, current-sim verdict, robustness-result, repair success, feasibility proof, checkpoint ranking, winner selection, checkpoint promotion, high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification
```

## Next

- next blocker: `m3151-engineering-controller-active-safety-driver-residual-action-delta-effectiveness-counterfactual-sensitivity-diagnostic-result-audit`
- follow-up manifest: `experiments/manifests/m3151-engineering-controller-active-safety-driver-residual-action-delta-effectiveness-counterfactual-sensitivity-diagnostic-result-audit.json`
