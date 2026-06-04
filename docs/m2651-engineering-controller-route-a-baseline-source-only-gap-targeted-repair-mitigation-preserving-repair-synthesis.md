# M2651 Engineering Controller Route A Source-Only Gap-Targeted Repair Mitigation-Preserving Repair Synthesis

- status: completed
- synthesis decision: `continue_to_mitigation_preserving_objective_design`
- next branch decision: `route_to_mitigation_preserving_repair_objective_design`
- manifest: `experiments/manifests/m2651-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-mitigation-preserving-repair-synthesis.json`
- parent summary: `runs/m2650_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_regression_localization/summary.json`
- parent findings: `runs/m2650_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_regression_localization/localization_findings.json`
- parent regression rows: `runs/m2650_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_regression_localization/mitigation_regression_rows.csv`
- follow-up manifest: `experiments/manifests/m2652-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-mitigation-preserving-objective-design.json`
- next: `m2652-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-mitigation-preserving-objective-design`

## Evidence Summary

M2651 accepts the M2648-M2650 Route A evidence as bounded source-only
engineering evidence for repair routing only.

Accepted facts:

```text
M2648 target_road_boundary_margin_control: 16/16 improved
M2648 target_drift_collision_recovery_tradeoff: 8/8 improved
M2648 protected_mitigation_reference: failed 7 improved / 1 regressed
M2650 matched protected mitigation pairs: 8
M2650 localized regressed row count: 1
M2650 regressed row: m2537_mitigation_preserving_policy unavoidable_mitigation seed 267101 fresh_fault_delay_noise
M2650 severity_proxy: 3.953864 -> 3.987916
M2650 likely component driver: obstacle_penetration_proxy_worsened
M2650 metric_artifact_detected: false
```

The regressed row worsened obstacle penetration even though several aggregate
proxies improved:

```text
minimum_obstacle_clearance_m: -1.436872 -> -1.477159
obstacle_penetration_proxy_m: 1.436872 -> 1.477159
collision_speed_proxy: 3.359023 -> 3.322625
impact_angle_proxy: 0.452959 -> 0.443488
minimum_road_margin_m: 0.899620 -> 0.949128
```

This means the M2648 repair direction improved admitted target gates but still
created a real protected-reference regression. The regression is not currently
explained as a metric artifact.

## Supported Claims

M2651 supports these bounded claims:

```text
M2648 produced behavior-changing Route A source-only repair evidence.
M2648 target gap gates improved in the proof smoke.
M2648 is not admissible for promotion or performance interpretation because a protected mitigation reference regressed.
M2650 localized the protected regression to seed 267101 fresh_fault_delay_noise and likely obstacle-penetration deepening.
The next safe route is a mitigation-preserving objective design before any second repair execution.
```

## Falsified Claims

M2651 rejects these claims:

```text
Target-gate improvement is sufficient for Route A baseline promotion.
The protected mitigation regression is acceptable collateral damage.
The protected mitigation regression is only a metric artifact.
Another repair execution can be run immediately without redesigning the objective and gates.
M2648 or M2650 proves driver performance, current-sim verdict, high-fidelity readiness, paper evidence, finite-window-vs-GRU evidence, or self-ID.
```

## Failure Taxonomy Summary

The active failure type is:

```text
behavior_regression
```

Localized form:

```text
protected_mitigation_reference regression
  subject: m2537_mitigation_preserving_policy
  role: unavoidable_mitigation
  seed: 267101
  dynamics_axis_id: fresh_fault_delay_noise
  likely driver: obstacle_penetration_proxy_worsened
```

Non-active but guarded failure types:

```text
metric_artifact: not supported by M2650, but M2652 should keep severity formula traceability explicit
objective_overfit: active risk if the next repair only optimizes road-boundary and drift target gates
proof_washout: active risk if mitigation_collision_saturated_reference is demoted from protected reference to ordinary target denominator
contract_violation: not observed; P0 72/3 and no-oracle actor boundary remain preserved
```

## Public Gate Overfit Risk

Risk is medium.

The M2648 repair improved admitted public target gates while regressing one
protected reference row. That is exactly the failure mode the post-M2470 Route
A split is meant to prevent: engineering repair can be useful, but it cannot
hide safety-reference regressions under aggregate target improvements.

The next objective must therefore be written as a multi-term protected repair
design, not another target-only repair execution:

```text
retain road-boundary and drift-recovery target improvements
add a protected mitigation non-regression term
make obstacle penetration a first-class protected component
keep mitigation_collision_saturated_reference protected, not a success denominator
keep axis_sensitivity_not_yet_decisive diagnostic-only
preserve actor input/output contract
```

## Next Branch Decision

Decision:

```text
continue_to_mitigation_preserving_objective_design
```

M2651 routes to M2652 mitigation-preserving repair objective design. M2652
should design the objective, row admissions, protected component gates, and
abort rules for a possible later repair execution.

M2652 must not run repair, training, reset, rollout, replay, validation, PPO,
source build, adapter probe, high-fidelity simulation, ranking, winner
selection, promotion, or success-rate verdict computation. It should only write
the objective design and follow-up route.

## Claim Boundary

M2651 is synthesis-only. It does not claim driver performance, promotion,
ranking, success rate, validation, paper evidence, finite-window-vs-GRU
evidence, current-sim verdict, high-fidelity validation, full ideal driver
completion, or self-ID.
