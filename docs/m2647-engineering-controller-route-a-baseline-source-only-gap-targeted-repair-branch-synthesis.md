# M2647 Engineering Controller Route A Source-Only Gap-Targeted Repair Branch Synthesis

- status: completed
- synthesis decision: `promote_to_next_branch`
- next branch decision: `promote_to_source_only_gap_targeted_repair_execution_preflight`
- manifest: `experiments/manifests/m2647-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-branch-synthesis.json`
- parent design: `docs/m2646-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-design.md`
- parent audit: `docs/m2645-engineering-controller-route-a-baseline-source-only-behavior-gap-taxonomy-materialization-result-audit.md`
- parent taxonomy summary: `runs/m2644_engineering_controller_route_a_source_only_behavior_gap_taxonomy/summary.json`
- route reference: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2648-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-execution-preflight.json`
- next: `m2648-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-execution-preflight`

## Evidence Summary

M2639-M2646 moved Route A from evidence indexing through fresh source-only
measurement, taxonomy, audit, and repair objective design.

Accepted branch evidence:

```text
M2639 evidence index refresh:
  status_pass: true
  evidence_index rows: 7
  gap_matrix rows: 5
  next_action_admission rows: 4
  selected_next_action: m2640_route_a_source_only_fresh_generalization_panel_design
  HF3 source dependency: paused at dependency_source_unavailable
  actor contract: P0 observation 72 / action 3

M2641 source-only fresh panel:
  status_pass: true
  role families: 4
  fresh seeds per role: 4
  dynamics axes: 2
  subjects: 5
  measured behavior rows: 160
  measured event rows: 160
  telemetry rows: 12800
  actor visibility guard rows: 19/19 pass
  gate matrix rows: 19/19 pass

M2644 behavior-gap taxonomy:
  status_pass: true
  source measured behavior rows: 160
  role gap rows: 4
  subject-role gap rows: 20
  dynamics-axis gap rows: 8
  repair-target admission rows: 4
  claim-boundary rows: 13
  gate matrix rows: 15/15 pass

M2645 audit:
  decision: accept_m2644_route_to_source_only_gap_targeted_repair_design

M2646 design:
  decision: route_to_source_only_gap_targeted_repair_branch_synthesis_before_materialization
```

The accepted repair-target map contains two repair-design targets:

```text
road_departure_dominant_gap:
  source rows: 80
  source roles: stable_aes, stable_avoidable
  target scope: road_boundary_margin_control

drift_recovery_mixed_gap:
  source rows: 40
  source roles: drift_required_recovery
  target scope: drift_collision_recovery_tradeoff
```

It also contains two protected non-target rows:

```text
mitigation_collision_saturated_reference:
  source rows: 40
  source role: unavoidable_mitigation
  disposition: reference_only

axis_sensitivity_not_yet_decisive:
  source rows: 160
  source roles: all four source-only roles
  disposition: diagnostic axis monitoring only
```

## Supported Claims

M2647 supports these bounded claims:

```text
M2639-M2646 produced a traceable Route A source-only diagnostic branch.
The source-only branch has enough accepted evidence to name two repair targets.
The admitted targets are road-boundary margin control and drift-collision-recovery tradeoff.
The branch preserved the P0 actor/action contract: observation 72, action 3.
Taxonomy labels, repair-target labels, route decisions, and source-only outcomes remain artifact metadata only.
The next useful evidence-producing step is a bounded repair execution preflight.
```

The branch does not need another static repair-plan materialization before
starting a bounded execution preflight. M2646 already defines objective
families, protected references, actor boundary, candidate row groups, and stop
rules. Another no-execution materialization would mostly duplicate that design
and extend the local-search loop that `research_validate` already flagged.

## Falsified Or Rejected Claims

M2647 rejects these interpretations:

```text
M2639-M2646 proves driver performance.
M2639-M2646 ranks controller families or selects a winner.
M2639-M2646 admits checkpoint promotion.
M2639-M2646 proves success-rate, validation, current-sim, high-fidelity, paper, or self-ID claims.
M2641 source-only fault/delay/noise metadata proves robust fault or validated delay/noise physics.
M2644 taxonomy labels or repair-target labels may enter actor input.
Unavoidable mitigation rows may be treated as ordinary success denominators.
Axis-sensitivity rows may be treated as repair targets or robust validation verdicts.
```

## Failure Taxonomy Summary

The active failure taxonomy is:

```text
road_departure_dominant_gap:
  failure types: behavior_regression, objective_overfit risk
  affected roles: stable_avoidable, stable_aes
  repair direction: road-boundary margin control without sacrificing clearance

drift_recovery_mixed_gap:
  failure types: behavior_regression, scenario_sampling_failure risk
  affected role: drift_required_recovery
  repair direction: balance collision avoidance, road margin, yaw/lateral velocity recovery,
    and command smoothness

mitigation_collision_saturated_reference:
  failure type if misused: metric_artifact
  protected role: unavoidable_mitigation
  repair direction: reference guard only, not a normal pass/fail denominator

axis_sensitivity_not_yet_decisive:
  failure type if overclaimed: metric_artifact
  protected scope: diagnostic axis monitoring only
  repair direction: monitor axis coverage, do not claim robust-fault or delay/noise verdict

actor-boundary risk:
  failure type: contract_violation
  protected invariant: observation 72 / action 3, no hidden/oracle actor inputs
```

## Public-Gate Overfit Risk

Risk is medium.

The branch has fresh source-only rows and did not optimize a single public proof
row. M2641 covered four roles, four fresh seeds per role, two source-only axes,
and five subjects. M2644/M2645 explicitly protected mitigation and axis rows
from denominator misuse.

The remaining overfit risk is workflow-level rather than row-level: after
M2643 the branch spent M2644-M2646 on taxonomy, audit, and design. Those were
useful, but another no-execution materialization would not add driver evidence.
The next step should produce bounded post-repair behavior evidence, while still
keeping proof/audit boundaries separate from ranking, validation, promotion, or
driver-performance claims.

## Next Branch Decision

Promote the workflow to a new branch:

```text
engineering_controller_route_a_source_only_gap_targeted_repair_execution
```

Register M2648:

```text
m2648-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-execution-preflight
```

M2648 should run one bounded source-only gap-targeted repair execution preflight
or record an implementation blocker. It may write a repaired checkpoint under
its run directory and measure post-repair source-only behavior rows. It must
preserve the P0 actor contract and must not rank controllers, select a winner,
promote a checkpoint, compute success-rate verdicts, validate, or claim driver
performance.

M2648 should use the accepted M2644/M2645/M2646 gap map:

```text
admitted targets:
  road_departure_dominant_gap
  drift_recovery_mixed_gap

protected references:
  mitigation_collision_saturated_reference
  axis_sensitivity_not_yet_decisive
```

Required M2648 evidence boundary:

```text
allowed:
  bounded source-only repair/training execution
  repaired checkpoint written only under the M2648 run directory
  post-repair source-only behavior rows
  repair training trace
  repair gate evaluation
  actor contract guard rows

forbidden:
  actor input change
  hidden/oracle actor inputs
  external high-fidelity simulation
  source build or adapter probe
  ranking, winner selection, promotion
  success-rate or controller-family verdict
  validation readiness/result
  driver-performance, paper, current-sim, high-fidelity, finite-window-vs-GRU, or self-ID claim
```

If M2648 cannot run without actor-contract changes or hidden/oracle inputs, it
should write a blocker or route to contract repair. If it runs and produces
post-repair evidence, the next milestone must audit the result before any
fresh/generalization or promotion interpretation.
