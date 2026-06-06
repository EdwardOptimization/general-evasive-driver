# M2943 Engineering Controller Route A Offtrack-Dominant Constraint-Balanced Candidate Implementation Design

## Summary

- status: completed
- decision: `admit_m2944_actor_head_delta_implementation_contract_materialization_preflight`
- manifest: `experiments/manifests/m2943-engineering-controller-route-a-offtrack-dominant-constraint-balanced-candidate-implementation-design.json`
- parent audit: `docs/m2942-engineering-controller-route-a-offtrack-dominant-constraint-balanced-candidate-materialization-result-audit.md`
- parent summary: `runs/m2941_engineering_controller_route_a_offtrack_dominant_constraint_balanced_candidate_materialization_preflight/summary.json`
- follow-up manifest: `experiments/manifests/m2944-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-implementation-contract-materialization-preflight.json`
- next: `m2944-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-implementation-contract-materialization-preflight`

M2943 converts the accepted M2941/M2942 materialized route into one bounded implementation design. It does not implement code, train, execute, validate, rank, promote, select a winner, or claim repair success.

## Selected Design

Selected implementation design:

```text
frozen_trunk_bounded_residual_actor_head_delta_design
```

The future candidate may define a deployable residual actor-head delta around an existing parent actor, but only under these constraints:

```text
actor observation shape: 72
action shape: 3
deployed action mapping: steer / throttle / brake
parent actor trunk and observation contract remain unchanged
residual head uses only deployable actor features available from the parent actor path
residual output is bounded before combining with parent action
zero residual must reproduce the parent action path
all evaluator constraints remain actor-invisible
no hidden/oracle/future-target actor input
no source/task/checkpoint/window/severity/time labels as actor input
no objective/constraint/diagnostic/success/verdict labels as actor input
```

M2943 does not choose numeric residual bounds, trainable tensors, optimizer settings, or checkpoint paths. M2944 must materialize those as explicit contract rows before any implementation work.

## Required Objective Bindings

The future implementation contract must bind the selected residual-head design to all M2941 objective families:

```text
persistent_offtrack_reduction:
  24 persistent offtrack rows must remain primary failure pressure.

collision_speed_anti_substitution:
  10 collision/speed substitution rows must block offtrack-only improvement claims.

success_context_retention:
  9 context-retention rows must block success-context regression hiding.

positive_reference_preservation:
  4 positive-reference rows remain diagnostic references only, not rankings.

full_panel_accounting:
  all 56 carryforward constraints remain evaluator-side accounting.
```

## Required Implementation Surface

M2944 must materialize this design into machine-checkable rows:

```text
implementation_surface_rows:
  one frozen_trunk_bounded_residual_actor_head_delta_design row.

delta_contract_rows:
  residual-head-only surface, bounded output, zero-delta fallback, parent-action preservation, no direct trunk rewrite.

objective_binding_rows:
  one row per M2941 objective family with expected source counts 24 / 10 / 9 / 4 / 56.

constraint_traceability_rows:
  all 56 M2941 carryforward constraints remain linked and actor-invisible.

actor_contract_guard_rows:
  observation 72, action 3, deployed action mapping unchanged, no oracle labels.

blocked_shortcut_rows:
  no direct full-policy retrain, no evaluator-label conditioning, no target-only offtrack loss, no replay-as-proof, no ranking, no promotion.

claim_boundary_rows:
  only implementation-contract materialization is allowed.

gate_matrix:
  all source, count, actor, shortcut, claim, follow-up, and artifact gates must pass.

follow_up_audit_manifest:
  M2944 must register a result audit before interpretation.
```

## Rejected Alternatives

```text
direct_candidate_implementation:
  rejected because implementation contracts are not materialized yet.

full_actor_or_trunk_rewrite:
  rejected because it expands the blast radius before a bounded actor-head contract is auditable.

target_only_offtrack_residual:
  rejected because it can hide collision/speed substitution and success-context regression.

evaluator_label_conditioned_actor:
  rejected because objective, constraint, route, diagnostic, success, and verdict labels are not deployable actor observations.

winner_selection_or_promotion:
  rejected because no implemented or validated candidate exists.
```

## Claim Boundary

M2943 is design-only. It does not implement a residual head, modify a checkpoint, run an environment, train a policy, validate a policy, rank candidates, select a winner, promote a checkpoint, or claim repair success.

Rejected claims:

```text
repair success
driver performance
validation readiness or result
source/task/checkpoint/environment/window/severity/time-band ranking
candidate ranking or winner selection
checkpoint promotion
success-rate verdict
paper evidence
finite-window-vs-GRU conclusion
current-sim verdict
high-fidelity validation readiness or result
full ideal driver completion
level3 self-identification
```
