# M2940 Engineering Controller Route A Offtrack-Dominant Tradeoff-Aware Candidate Design

## Summary

- status: completed
- decision: `admit_m2941_constraint_balanced_candidate_materialization_preflight`
- manifest: `experiments/manifests/m2940-engineering-controller-route-a-offtrack-dominant-tradeoff-aware-candidate-design.json`
- parent synthesis: `docs/m2939-engineering-controller-route-a-offtrack-dominant-post-materialization-continuation-or-stop-synthesis.md`
- parent materialization: `runs/m2937_engineering_controller_route_a_offtrack_dominant_tradeoff_aware_repair_redesign_materialization_preflight/summary.json`
- follow-up manifest: `experiments/manifests/m2941-engineering-controller-route-a-offtrack-dominant-constraint-balanced-candidate-materialization-preflight.json`
- next: `m2941-engineering-controller-route-a-offtrack-dominant-constraint-balanced-candidate-materialization-preflight`

M2940 converts the M2939 synthesis into one bounded candidate route. The candidate is not a checkpoint, not a training run, and not an execution result. It is a no-execution design for a future actor-head delta repair candidate whose evaluator-side objective must balance persistent offtrack reduction, collision/speed anti-substitution, context retention, and positive-reference preservation.

## Candidate Route

Selected route:

```text
constraint_balanced_actor_head_delta_candidate
```

This route is allowed to define a future candidate recipe that modifies only the deployable actor head or bounded actor-head delta surface while preserving:

```text
actor observation shape: 72
action shape: 3
deployed action mapping: steer / throttle / brake
no hidden/oracle/future-target actor input
no source/task/checkpoint/window/severity/time labels as actor input
no evaluator constraint labels as actor input
```

The route is not allowed to execute, train, validate, rank, select a winner, or promote anything inside M2940.

## Required Constraint Families

The candidate route must carry all M2937 constraint families forward:

```text
full panel accounting:
  preserve all 56 transition rows.

persistent offtrack pressure:
  account for 24 offtrack->offtrack rows.

collision/speed substitution guard:
  account for 10 offtrack->collision or offtrack->speed_too_low rows.

context-retention guard:
  account for 9 success->offtrack or success->collision rows.

positive-reference preservation:
  preserve 4 offtrack->success rows as diagnostic references, not rankings.
```

## Candidate Design Surface

M2940 defines one future materialization surface with these rows:

```text
candidate_route_row:
  one route row naming constraint_balanced_actor_head_delta_candidate.

objective_balance_rows:
  persistent_offtrack_reduction
  collision_speed_anti_substitution
  success_context_retention
  positive_reference_preservation
  full_panel_accounting

constraint_carryforward_rows:
  every M2937 transition constraint remains actor-invisible and evaluator-side.

actor_contract_rows:
  observation 72, action 3, deployed action mapping unchanged, no oracle labels.

blocked_shortcut_rows:
  no target-only objective, no aggregate offtrack-only success, no candidate ranking, no fixed-candidate replay as proof.

follow_up_audit_manifest:
  M2941 must register a result audit before interpretation.
```

## Rejected Alternatives

```text
direct_fixed_candidate_execution:
  rejected because M2939 explicitly requires design before execution and M2931/M2934 already exposed mixed fixed-candidate tradeoffs.

target_only_offtrack_objective:
  rejected because it can reduce offtrack by increasing collision, speed_too_low, or context regressions.

constraint_label_actor_input:
  rejected because evaluator-side labels are not deployable observations.

winner_selection_or_ranking:
  rejected because no validated candidate exists.

branch_stop:
  rejected for now because M2937/M2939 define a bounded actor-safe design route that changes the repair question.
```

## M2941 Requirements

M2941 must materialize, without execution or training:

```text
candidate_route_rows
objective_balance_rows
constraint_carryforward_rows
blocked_shortcut_rows
actor_contract_guard_rows
claim_boundary_rows
gate_matrix
run_state
follow-up audit manifest
```

M2941 must preserve the exact M2937 counts:

```text
transition constraints: 56
persistent offtrack constraints: 24
collision/speed substitution constraints: 10
context-retention constraints: 9
positive reference rows: 4
candidate-surface rows: 5
```

## Claim Boundary

M2940 is design-only. It does not execute an environment, train a policy, validate a policy, rank candidates, select a winner, promote a checkpoint, or claim repair success.

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
