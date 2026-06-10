# M3177 Behavior-Negative Targeted Trace-Ablation Materialization Preflight

## Summary

- status: completed
- result class: `active_safety_driver_behavior_negative_targeted_trace_ablation_materialization_pass`
- target regression rows: 1
- trace rows: 443
- ablation variants: 5
- candidate outcome: `collision_failure`
- incumbent outcome: `success_obstacle_pass`
- candidate clearance margin: -0.11747365908727159
- incumbent clearance margin: 0.2678248895862312
- gate matrix pass: True

## Interpretation

M3177 re-executes only the selected M3172 new collision regression row with actor-visible direct-action variants. Row labels and incumbent outcomes select the experimental sample but are not actor runtime inputs. The artifacts are trace-ablation evidence only and do not implement a repair or validate a driver.

Rejected claims:

```text
repair implementation, validation result, driver-performance verdict, current-sim verdict, robustness-result, repair success, feasibility proof, checkpoint ranking, winner selection, checkpoint promotion, public driver default replacement, high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification
```

## Next

- next blocker: `m3178-engineering-controller-active-safety-driver-residual-hard-safety-behavior-negative-targeted-trace-ablation-result-audit`
- follow-up manifest: `experiments/manifests/m3178-engineering-controller-active-safety-driver-residual-hard-safety-behavior-negative-targeted-trace-ablation-result-audit.json`
