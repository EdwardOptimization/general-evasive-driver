# M3153 Residual Action-Delta Counterfactual Replay Diagnostic

## Summary

- status: completed
- result class: `active_safety_driver_residual_action_delta_counterfactual_replay_diagnostic_materialization_pass`
- residual replay plan rows: 7/7
- fixed variant rows: 4
- counterfactual episode rows: 28
- counterfactual failure rows: 0
- comparison rows: 21
- action-channel-sensitive diagnostic comparisons: 0
- gate matrix pass: True

## Variant Terminal Counts

- brake_saturation_probe: {'success': 0, 'collision': 5, 'offtrack': 2, 'speed_too_low': 0}
- decel_headroom_probe: {'success': 0, 'collision': 5, 'offtrack': 2, 'speed_too_low': 0}
- lateral_headroom_probe: {'success': 0, 'collision': 5, 'offtrack': 2, 'speed_too_low': 0}
- m3142_reference: {'success': 0, 'collision': 5, 'offtrack': 2, 'speed_too_low': 0}

## Diagnostic Labels

- counterfactual_terminal_outcome_unchanged_diagnostic: 21

## Interpretation

M3153 replays only the seven residual rows with fixed predeclared actor-visible direct-action variants. The replay rows diagnose whether residual terminal behavior is sensitive to bounded action-channel changes. They are not a repair implementation, validation, ranking, promotion, repair-success, robustness-result, driver-performance, current-sim verdict, high-fidelity, paper, finite-window-vs-GRU, full-driver, feasibility-proof, or self-ID evidence.

Rejected claims:

```text
repair implementation, validation result, driver-performance verdict, current-sim verdict, robustness-result, repair success, feasibility proof, checkpoint ranking, winner selection, checkpoint promotion, high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification
```

## Next

- next blocker: `m3154-engineering-controller-active-safety-driver-residual-action-delta-counterfactual-replay-diagnostic-result-audit`
- follow-up manifest: `experiments/manifests/m3154-engineering-controller-active-safety-driver-residual-action-delta-counterfactual-replay-diagnostic-result-audit.json`
