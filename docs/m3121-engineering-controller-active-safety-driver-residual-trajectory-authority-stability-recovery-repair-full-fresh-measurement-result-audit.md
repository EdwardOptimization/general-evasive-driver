# M3121 Residual Trajectory-Authority Stability-Recovery Measurement Result Audit

## Decision

- decision: `accept_m3120_artifacts_with_plateau_route_to_m3122_residual_trajectory_authority_stability_recovery_plateau_synthesis`
- selected next action: `m3122-engineering-controller-active-safety-driver-residual-trajectory-authority-stability-recovery-repair-plateau-synthesis`
- result class: `accept_m3120_artifacts_with_residual_hard_safety_plateau`

## Evidence Summary

M3120 is complete and claim-safe as a full-fresh measurement artifact:

```text
status_pass: True
gate_matrix_pass: True
required_artifacts_present: True
scheduled rows: 64/64
measurement episode rows: 64
measurement failure rows: 0
same-row comparison rows: 256
exact seed matches: M3105=64, M3095=64, M3100=64, M3090=64
actor: 72/action 3 direct_action_clipped [steer throttle brake]
runtime_base_policy_required: False
checkpoint_model_required: False
recurrent_hidden_state_required: False
```

The behavior result remains a plateau against the strongest no-regression baselines:

```text
success: 57
collision: 5
offtrack: 2
speed_too_low: 0
success_delta_vs_m3105: 0
collision_delta_vs_m3105: 0
offtrack_delta_vs_m3105: 0
speed_too_low_delta_vs_m3105: 0
success_delta_vs_m3095: 0
collision_delta_vs_m3095: 0
offtrack_delta_vs_m3095: 0
speed_too_low_delta_vs_m3095: 0
```

M3120 improves versus older M3090 and M3100 in the same-row context, but it does not improve the current hard-safety blocker over M3105/M3095/M3112. The residual blocker remains five obstacle collisions and two off-track terminations with zero speed-too-low failures.

## Accepted Claims

- M3120 produced complete full-fresh measurement artifacts for the M3118 direct-action function.
- The obs72/action3 direct-action boundary and no-runtime-base-policy boundary are preserved.
- Same-row comparison artifacts exist for M3105, M3095, M3100, and M3090 with complete seed identity.
- M3120 is behavior-negative for the active repair objective because it leaves the same 5 collision and 2 offtrack blockers versus M3105/M3095.

## Rejected Claims

- M3120 is not repair-success evidence.
- M3120 is not validation, ranking, promotion, robustness-result, driver-performance, current-sim verdict, high-fidelity, paper, full-driver, or self-ID evidence.
- The M3118 trajectory-authority/stability-recovery rule set should not be promoted or interpreted as an improvement over M3105/M3095.
- Continuing with another blind direct-rule gain edit would repeat the same local-search failure mode without changing the evidence axis.

## Failure Taxonomy

- `contract_violation`: not observed; actor/action/runtime dependency contracts pass.
- `lineage_invalid`: not observed; M3120 follows M3119/M3118 and registers M3121.
- `metric_artifact`: not observed; row counts, gate matrix, comparison rows, and metric summaries are complete.
- `scenario_sampling_failure`: not observed; the complete 64-row M3084 denominator is preserved.
- `behavior_regression`: not observed relative to M3105/M3095 counts, but no residual hard-safety improvement is observed.
- `objective_overfit`: high risk if the branch continues with another same-row overlay gain edit.
- `proof_washout`: high risk if complete measurement artifacts are described as repair success.
- `seed_fragility`: unresolved; no validation/generalization claim is allowed.

## Next

Route to M3122 plateau synthesis. M3122 must decide whether to stop this direct-rule repair branch, pivot to a different action-authority/feasibility diagnostic, or register exactly one next route. It must not claim validation, ranking, promotion, repair-success, robustness-result, driver-performance, current-sim verdict, high-fidelity, paper, full-driver, or self-ID evidence.
