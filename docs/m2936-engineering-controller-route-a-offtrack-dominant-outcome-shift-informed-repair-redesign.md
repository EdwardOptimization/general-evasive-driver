# M2936 Engineering Controller Route A Offtrack-Dominant Outcome-Shift-Informed Repair Redesign

## Summary

- status: completed
- decision: `admit_m2937_tradeoff_aware_repair_redesign_materialization_preflight`
- manifest: `experiments/manifests/m2936-engineering-controller-route-a-offtrack-dominant-outcome-shift-informed-repair-redesign.json`
- parent audit: `docs/m2935-engineering-controller-route-a-offtrack-dominant-repair-execution-outcome-shift-localization-result-audit.md`
- parent summary: `runs/m2934_engineering_controller_route_a_offtrack_dominant_repair_execution_outcome_shift_localization_preflight/summary.json`
- follow-up manifest: `experiments/manifests/m2937-engineering-controller-route-a-offtrack-dominant-tradeoff-aware-repair-redesign-materialization-preflight.json`
- next: `m2937-engineering-controller-route-a-offtrack-dominant-tradeoff-aware-repair-redesign-materialization-preflight`

M2936 converts the accepted M2934/M2935 localization into a changed repair question. The next route is not another fixed-candidate execution. It is a no-execution materialization of a tradeoff-aware redesign surface that treats offtrack reduction, collision/speed substitution, and context retention as simultaneous constraints.

## Input Evidence

M2934/M2935 established this row-level outcome-shift surface:

```text
panel rows: 56
offtrack target rows: 38
non-offtrack context rows: 18

offtrack -> success: 4
offtrack -> offtrack: 24
offtrack -> collision: 4
offtrack -> speed_too_low: 6

success -> offtrack: 5
success -> collision: 4
success -> success: 2

collision -> collision: 1
collision -> offtrack: 1
collision -> speed_too_low: 1

speed_too_low -> speed_too_low: 3
speed_too_low -> offtrack: 1
```

The M2655 fixed candidate is therefore not a repair-success result. It exposes four useful offtrack-to-success examples, but most offtrack rows remain offtrack or shift into collision/speed failure, and many previously successful context rows regress.

## Redesign Requirements

The next repair route must satisfy all of these constraints:

```text
R1 full-panel accounting: keep all 56 M2925 panel rows visible.
R2 offtrack target accounting: preserve all 38 offtrack target rows.
R3 context accounting: preserve all 18 non-offtrack context rows.
R4 persistent-offtrack pressure: explicitly cover the 24 offtrack->offtrack rows.
R5 substitution guard: explicitly cover the 10 offtrack->collision/speed_too_low rows.
R6 context-retention guard: explicitly cover the 9 success->offtrack/collision rows.
R7 positive-row preservation: preserve the 4 offtrack->success rows as diagnostic exemplars, not as rankings.
R8 actor contract: keep observation 72/action 3 and no hidden/oracle/future-target actor input.
R9 no ranking: source/task/checkpoint/window/severity/time aggregates are constraints, not rankings.
R10 no overclaim: no repair-success, validation, performance, paper, high-fidelity, full-driver, finite-window-vs-GRU, or self-ID claim.
```

## Selected Redesign

M2936 selects one redesign surface:

```text
tradeoff_aware_repair_redesign_materialization
```

The surface has four evaluator-side constraint families:

```text
offtrack_persistence_constraint:
  covers offtrack->offtrack rows and requires any future repair design to target persistent lateral/offtrack failure directly.

collision_speed_substitution_constraint:
  covers offtrack->collision and offtrack->speed_too_low rows and blocks designs that reduce offtrack by converting it into collision or low-speed failure.

context_retention_constraint:
  covers success->offtrack and success->collision rows and blocks designs that improve target rows while degrading previously successful context rows.

positive_transition_reference:
  preserves offtrack->success rows as diagnostic references, not as candidate rankings or promotion evidence.
```

The materialized surface must be actor-invisible. These row labels, constraints, source/task bands, and transition buckets can be used by the research harness to design and audit future repair candidates, but they must not become actor input.

## Rejected Alternatives

```text
direct_fixed_candidate_execution:
  rejected because M2931 already executed the fixed candidate and M2934 shows mixed regressions.

target_only_offtrack_repair:
  rejected because it would ignore collision/speed substitution and success-context regression.

source_or_task_ranking:
  rejected because M2934 aggregates are diagnostic constraints, not winners.

validation_or_performance_gate:
  rejected because no repaired policy or stable candidate exists.

branch_stop:
  rejected for now because M2934 provides a materially changed repair question that can be materialized without execution.
```

## Next Materialization

M2937 must materialize, without execution or training:

```text
transition_constraint_rows
offtrack_persistence_constraint_rows
collision_speed_substitution_constraint_rows
context_retention_constraint_rows
positive_transition_reference_rows
candidate_surface_rows
actor_contract_guard_rows
claim_boundary_rows
gate_matrix
run_state
follow-up audit manifest
```

M2937 must register M2938 result audit before any interpretation.

## Claim Boundary

M2936 is a design-only milestone. It does not execute an environment, train a policy, validate a policy, rank rows, select a winner, promote a checkpoint, or claim repair success.

Rejected claims:

```text
repair success
driver performance
validation readiness or result
source/task/checkpoint/environment/window/severity/time-band ranking
winner selection
checkpoint promotion
success-rate verdict
paper evidence
finite-window-vs-GRU conclusion
current-sim verdict
high-fidelity validation readiness or result
full ideal driver completion
level3 self-identification
```
