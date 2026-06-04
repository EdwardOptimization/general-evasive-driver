# M2656 Engineering Controller Route A Mitigation-Preserving Repair Execution Branch Synthesis

- status: completed
- synthesis decision: `pivot`
- next branch decision: `pivot_to_route_a_source_only_target_protected_tradeoff_report`
- manifest: `experiments/manifests/m2656-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-mitigation-preserving-repair-execution-branch-synthesis.json`
- parent execution summary: `runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/summary.json`
- parent candidate sweep: `runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/repair_candidate_sweep.csv`
- parent gate evaluation: `runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/mitigation_preserving_gate_evaluation.csv`
- route reference: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2657-engineering-controller-route-a-baseline-source-only-target-protected-tradeoff-report-materialization-preflight.json`
- next: `m2657-engineering-controller-route-a-baseline-source-only-target-protected-tradeoff-report-materialization-preflight`

## Evidence Summary

M2656 synthesizes the Route A source-only gap-targeted repair branch after the
M2655 gate-aware repair execution repeated the protected mitigation failure.

Behavior-changing evidence:

```text
M2648:
  repair_execution_started: true
  checkpoint_behavior_changed: true
  post_repair_behavior_rows: 160
  target_road_boundary_margin_control: pass, 16/16 improved
  target_drift_collision_recovery_tradeoff: pass, 8/8 improved
  protected_mitigation_reference: fail, 7 improved / 1 regressed
  actor contract: P0 observation 72 / action 3, no hidden/oracle actor input
```

Protected regression localization:

```text
M2650:
  regressed row: m2537_mitigation_preserving_policy unavoidable_mitigation seed 267101 fresh_fault_delay_noise
  severity_proxy: 3.953864 -> 3.987916
  severity_delta: +0.034052
  likely component driver: obstacle_penetration_proxy_worsened
  metric_artifact_detected: false
```

Gate-aware repair execution:

```text
M2655:
  status_pass: true
  repair candidates: 3
  selected diagnostic candidate: m2655_softened_gap_bias
  post_repair_behavior_rows: 160
  telemetry_rows: 12800
  target_preservation_gates_all_passed: true
  protected_component_gates_all_passed: false
  target_and_protected_gates_all_passed: false
  failed protected gates:
    severity_proxy_non_regression
    obstacle_penetration_non_regression
    minimum_obstacle_clearance_preservation
```

M2655 keeps the actor/action and no-oracle boundary intact, but all three
candidate rows have the same high-level outcome: target preservation passes
while protected mitigation components fail.

## Supported Claims

M2656 supports these bounded claims:

```text
The source-only repair branch produced real behavior-changing evidence.
Road-boundary and drift-recovery target rows can be improved or preserved by the tested bias repair family.
The tested repair family still fails protected mitigation non-regression.
M2655 status_pass means the preflight artifacts are complete and traceable, not that the repair succeeded.
The selected M2655 candidate is diagnostic only; it is not a winner and is not promoted.
The actor contract remains P0 observation 72 / action 3 with no hidden/oracle actor inputs.
The next useful Route A step is evidence reanalysis for scenario-role target/protected tradeoff, not another same-row repair.
```

This remains Route A engineering process evidence. It does not prove driver
performance, validation readiness, paper evidence, finite-window-vs-GRU,
current-sim verdict, high-fidelity validation, full ideal driver completion, or
self-identification.

## Falsified Claims

M2656 rejects these interpretations:

```text
Target gate preservation is enough for repair success.
M2655 status_pass is a promotion or performance signal.
The selected M2655 diagnostic candidate is a winner.
The severity, obstacle-penetration, and clearance protected failures are optional.
Another same-row public candidate sweep is justified before synthesis changes the evidence axis.
The protected mitigation row can be treated as an ordinary success denominator.
Weakening protected mitigation gates is an acceptable way to preserve target improvements.
The M2648-M2655 branch proves driver performance, validation, paper, finite-window-vs-GRU, current-sim, high-fidelity, or self-ID claims.
```

## Failure Taxonomy Summary

Active failure:

```text
behavior_regression:
  repeated count: 3
  form: protected mitigation severity / obstacle penetration / clearance regression
  M2655 failed gates:
    severity_proxy_non_regression: 1/8 regressed, max regression delta 0.025451
    obstacle_penetration_non_regression: 2/8 regressed, max regression delta 0.027610
    minimum_obstacle_clearance_preservation: 2/8 regressed, max regression delta 0.027610
```

Active process risk:

```text
objective_overfit:
  same public repair loop count: 3
  evidence: M2648 target-only repair and M2655 gate-aware repair both retain target improvements while protected mitigation fails

proof_washout:
  risk if protected mitigation gates are weakened to keep target improvements

metric_artifact:
  not supported by M2650; the protected failure is behavior-level

contract_violation:
  not observed in M2655; actor P0 72/3 and no hidden/oracle boundary remain intact
```

## Public-Gate Overfit Risk

Risk is now high for any immediate continuation of the same repair loop.
M2648 already showed target gains with a protected mitigation regression, and
M2655 shows that adding the M2653 protected gates does not make the tested
bias-repair family preserve mitigation. The public target rows are useful
diagnostics, but continuing to tune the same source-only candidate family would
optimize visible gates without adding a new evidence axis.

The repair branch should close here. The next work should preserve the M2655
negative result and convert the Route A evidence into a scenario-role
target/protected tradeoff report. That report should make the engineering
baseline boundary explicit:

```text
where target behavior improves
where protected mitigation regresses
which scenario roles are repair targets versus protected references
which metrics block promotion or performance claims
which next evidence route is non-overfit
```

## Next Branch Decision

Decision:

```text
pivot_to_route_a_source_only_target_protected_tradeoff_report
```

Register M2657:

```text
m2657-engineering-controller-route-a-baseline-source-only-target-protected-tradeoff-report-materialization-preflight
```

M2657 should consume existing Route A source-only evidence only:

```text
M2641 baseline behavior rows
M2648 target-only repair post rows and gates
M2655 mitigation-preserving repair post rows, candidate sweep, and gates
M2650 protected regression localization
```

M2657 should materialize a scenario-role metric report that separates target
gains from protected mitigation regressions. It must not run another repair,
train, rank candidates, promote checkpoints, compute success-rate verdicts, or
claim driver performance.

## Claim Boundary

M2656 is synthesis-only. It did not run repair, training, reset, step, rollout,
replay, validation, PPO, source build, adapter probe, external simulation,
ranking, winner selection, promotion, or success-rate computation.

No driver-performance, paper-level, finite-window-vs-GRU, current-sim,
high-fidelity validation, full ideal driver, or self-ID claim is made.
