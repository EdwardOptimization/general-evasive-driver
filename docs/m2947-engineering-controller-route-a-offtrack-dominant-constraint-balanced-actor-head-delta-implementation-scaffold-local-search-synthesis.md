# M2947 Engineering Controller Route A Offtrack-Dominant Constraint-Balanced Actor-Head Delta Implementation Scaffold Local-Search Synthesis

## Summary

- status: completed
- decision: `continue_to_m2948_bounded_actor_head_delta_implementation_scaffold`
- manifest: `experiments/manifests/m2947-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-implementation-scaffold-local-search-synthesis.json`
- parent admission: `docs/m2946-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-implementation-admission-design.md`
- next manifest: `experiments/manifests/m2948-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-implementation-scaffold.json`
- next: `m2948-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-implementation-scaffold`

M2947 synthesizes the M2940-M2946 Route A actor-head delta implementation-admission chain after the local-search guard blocks another direct non-evidence milestone. It continues to exactly one bounded code-scaffold milestone, M2948. It does not implement code, mutate checkpoints, execute an environment, train, validate, rank, promote, or claim implementation readiness, repair success, driver performance, paper evidence, high-fidelity readiness, full-driver completion, finite-window-vs-GRU evidence, or self-ID evidence.

## Synthesis Questions

### evidence_summary

The current branch has moved through bounded non-execution milestones:

```text
M2940: selected one constraint-balanced actor-head delta candidate design.
M2941: materialized candidate route, objective-balance, carryforward, shortcut, actor, claim, and gate rows.
M2942: accepted M2941 as complete and claim-safe.
M2943: selected frozen_trunk_bounded_residual_actor_head_delta_design.
M2944: materialized implementation surface, delta contract, objective binding, traceability, shortcut, actor, claim, and gate rows.
M2945: accepted M2944 as complete and claim-safe.
M2946: admitted one bounded scaffold route, but only after local-search synthesis.
```

The accepted M2944/M2945 evidence remains:

```text
implementation surface rows: 1
delta contract rows: 7
objective binding rows: 5
constraint traceability rows: 56
blocked shortcut rows: 8
actor contract guards: 19
claim boundary rows: 30
gate matrix pass: true
```

The branch has enough contract evidence to open one scaffold milestone, but not enough closed-loop or validation evidence for implementation readiness or performance claims.

### supported_claims

Supported claims:

```text
one bounded residual actor-head delta scaffold route remains admissible
actor observation shape 72 and action shape 3 must remain unchanged
zero-delta parent-action identity and residual bound enforcement are mandatory scaffold tests
M2948 may add code and unit tests only, not checkpoint or environment execution
local-search guard is satisfied by this synthesis before the next non-evidence milestone
```

### falsified_claims

Not supported and therefore rejected:

```text
implementation readiness
repair success
driver performance
validation readiness or validation result
candidate ranking or winner selection
checkpoint promotion
paper evidence
current-sim or high-fidelity verdict
finite-window-vs-GRU conclusion
full ideal driver completion
level3 self-identification
```

### failure_taxonomy_summary

The active risk is process/local-search overproduction, not a new empirical driver failure. The synthesis keeps `same_failure_repeat_count=1`, `same_public_gate_repair_count=0`, and `local_search_risk=medium`. It blocks the shortcut of increasing `non_evidence_streak_limit` to force a direct scaffold milestone through validation.

### public_gate_overfit_risk

No public proof row, rollout, replay, or validation gate is executed in M2947. The overfit risk is procedural: continuing to add design artifacts without code or evidence would inflate the branch without changing what can be tested. M2948 is therefore limited to scaffold code and focused unit tests, followed by a result audit before any candidate execution or interpretation.

### implementation_scaffold_admission

M2948 is admitted with the following hard boundaries:

```text
allowed:
  add src/autodrift/constraint_balanced_actor_head_delta_scaffold.py
  add tests/test_constraint_balanced_actor_head_delta_scaffold.py
  add docs/m2948-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-implementation-scaffold.md

required tests:
  actor observation shape 72 -> action shape 3
  zero residual reproduces parent actor output
  residual delta is bounded before action combination
  forbidden evaluator/privileged input labels are rejected
  no checkpoint load/modify/save/rank/promote side effects
  no environment reset/step/rollout/replay/validation/training side effects

blocked:
  checkpoint mutation
  reset/step/rollout/replay/validation/training/PPO/dependency work
  evaluator-label actor conditioning
  candidate ranking/promotion
  implementation readiness, repair-success, performance, paper, high-fidelity, full-driver, finite-window-vs-GRU, or self-ID claims
```

### next_branch_decision

Decision:

```text
continue_to_m2948_bounded_actor_head_delta_implementation_scaffold
```

M2948 should be the only immediate follow-up. If M2948 cannot preserve the actor contract, zero-delta identity, residual bounds, forbidden-input boundary, and no-side-effect boundary, the branch should route to audit/repair or stop rather than continue into execution.
