# M2654 Engineering Controller Route A Mitigation-Preserving Objective Materialization Branch Synthesis

- status: completed
- synthesis decision: `continue`
- next branch decision: `continue_to_mitigation_preserving_repair_execution_preflight`
- manifest: `experiments/manifests/m2654-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-mitigation-preserving-objective-materialization-branch-synthesis.json`
- parent execution summary: `runs/m2648_engineering_controller_route_a_source_only_gap_targeted_repair_execution/summary.json`
- parent localization summary: `runs/m2650_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_regression_localization/summary.json`
- parent localization findings: `runs/m2650_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_regression_localization/localization_findings.json`
- parent objective materialization summary: `runs/m2653_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_objective_materialization/summary.json`
- route reference: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2655-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-mitigation-preserving-repair-execution-preflight.json`
- next: `m2655-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-mitigation-preserving-repair-execution-preflight`

## Evidence Summary

M2654 synthesizes M2648-M2653 Route A evidence after the local-search guard
rejected another non-evidence audit step.

Accepted behavior evidence:

```text
M2648:
  repair_execution_started: true
  repair_training_started: true
  checkpoint_behavior_changed: true
  post_repair_behavior_rows: 160
  target_road_boundary_margin_control: 16/16 improved
  target_drift_collision_recovery_tradeoff: 8/8 improved
  protected_mitigation_reference: failed, 7 improved / 1 regressed
  actor contract: P0 observation 72 / action 3, no hidden/oracle input
```

Accepted protected-regression localization:

```text
M2650:
  matched protected mitigation pairs: 8
  regressed rows: 1
  regressed row: m2537_mitigation_preserving_policy unavoidable_mitigation seed 267101 fresh_fault_delay_noise
  severity_proxy: 3.953864 -> 3.987916
  minimum_obstacle_clearance_m: -1.436872 -> -1.477159
  obstacle_penetration_proxy_m: 1.436872 -> 1.477159
  collision_speed_proxy: 3.359023 -> 3.322625
  impact_angle_proxy: 0.452959 -> 0.443488
  metric_artifact_detected: false
  likely component driver: obstacle_penetration_proxy_worsened
```

Accepted process and artifact evidence:

```text
M2651:
  rejects immediate second repair execution
  routes to mitigation-preserving objective design

M2652:
  defines road_boundary_margin_target
  defines drift_collision_recovery_target
  defines mitigation_non_regression_protected
  requires severity, obstacle penetration, clearance, and event-transition protected gates

M2653:
  objective family rows: 3
  protected component gate rows: 4
  target preservation gate rows: 2
  abort rule rows: 9
  actor contract guard rows: 6
  claim boundary rows: 25
  gate matrix rows: 10
  gate_matrix_pass: true
```

## Supported Claims

M2654 supports these bounded claims:

```text
M2648 produced real source-only closed-loop repair evidence and changed behavior.
M2648 target improvements are real enough to retain as target-preservation gates.
M2648 is not admissible as a promoted baseline because a protected mitigation row regressed.
M2650 shows the protected regression is a real behavior regression, not a metric artifact.
M2653 provides a complete mitigation-preserving objective/gate bundle for a bounded next repair execution.
The next useful step is one gate-aware mitigation-preserving repair execution preflight.
```

This is still Route A engineering evidence. It does not prove driver
performance, validation readiness, paper evidence, finite-window-vs-GRU,
current-sim verdict, high-fidelity validation, or self-identification.

## Falsified Claims

M2654 rejects these interpretations:

```text
Target-gate improvement is enough for promotion.
The protected mitigation regression is acceptable collateral damage.
Collision speed or impact angle improvement is enough to pass protected mitigation when obstacle penetration deepens.
M2653 objective rows are behavior evidence by themselves.
Another target-only repair execution is admissible.
Protected mitigation rows may be treated as ordinary success denominators.
Objective, localization, taxonomy, route, or gate labels may enter actor input.
M2648-M2653 proves driver performance, validation, paper, finite-window-vs-GRU, current-sim, high-fidelity, or self-ID claims.
```

## Failure Taxonomy Summary

Active failure:

```text
behavior_regression:
  form: protected_mitigation_reference regression
  localized component: obstacle_penetration_proxy_worsened
  row: unavoidable_mitigation seed 267101 fresh_fault_delay_noise
```

Guarded failure risks:

```text
objective_overfit:
  risk if M2655 optimizes only road-boundary and drift target gates

proof_washout:
  risk if mitigation_non_regression_protected is weakened or demoted

contract_violation:
  risk if objective or gate metadata becomes actor-visible

metric_artifact:
  currently not supported by M2650, but severity and obstacle-penetration formulas must stay traceable

scenario_sampling_failure:
  risk if one protected public row becomes the only protected criterion
```

## Public-Gate Overfit Risk

Risk is high if the next milestone is another target-only public repair. M2648
already shows the failure mode: admitted target rows improved while one
protected mitigation row worsened. Continuing without M2653 protected component
gates would overfit the public target gates.

Risk is acceptable for exactly one bounded M2655 execution if M2655:

```text
consumes M2653 objective and protected component gate artifacts
evaluates severity_proxy_non_regression
evaluates obstacle_penetration_non_regression
evaluates minimum_obstacle_clearance_preservation
evaluates event_transition_guard
retains road-boundary and drift-recovery target-preservation gates
records candidate sweep rows before selecting any candidate
records no hidden/oracle actor input and P0 72/3 actor/action boundary
does not rank controllers, select a winner, promote, compute success-rate verdicts, or claim performance
routes to audit/synthesis if protected gates fail again
```

## Next Branch Decision

Decision:

```text
continue_to_mitigation_preserving_repair_execution_preflight
```

Register M2655:

```text
m2655-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-mitigation-preserving-repair-execution-preflight
```

M2655 may run one bounded source-only repair execution preflight. Unlike M2648,
it must be gate-aware: the repair executor must consume the M2653 materialized
objective/gate artifacts and treat the protected mitigation components as
blocking non-regression gates.

M2655 should produce behavior evidence, not another prose-only design:

```text
required behavior artifacts:
  repair_candidate_sweep.csv
  selected_repair_trace.csv
  repaired_checkpoint_manifest.json
  post_repair_behavior_rows.csv
  mitigation_preserving_gate_evaluation.csv
  repair_config_snapshot.json
  summary.json
```

M2655 must stop or route to audit/synthesis if no candidate preserves protected
mitigation gates while retaining the road-boundary and drift-recovery target
gates. It must not weaken the actor contract, use hidden/oracle features, rank
controller families, select a winner, promote a checkpoint, compute success
rate, claim validation, or claim driver performance.

## Claim Boundary

M2654 is synthesis-only. It did not run repair, training, reset, step, rollout,
replay, validation, PPO, source build, adapter probe, external simulation,
ranking, winner selection, promotion, or success-rate computation.

No driver-performance, paper-level, finite-window-vs-GRU, current-sim,
high-fidelity validation, full ideal driver, or self-ID claim is made.
