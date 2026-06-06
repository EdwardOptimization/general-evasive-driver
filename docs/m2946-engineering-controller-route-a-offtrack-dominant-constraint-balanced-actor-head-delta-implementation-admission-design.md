# M2946 Engineering Controller Route A Offtrack-Dominant Constraint-Balanced Actor-Head Delta Implementation Admission Design

## Summary

- status: completed
- decision: `admit_m2947_scaffold_local_search_synthesis_before_m2948_scaffold`
- manifest: `experiments/manifests/m2946-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-implementation-admission-design.json`
- parent audit: `docs/m2945-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-implementation-contract-materialization-result-audit.md`
- parent summary: `runs/m2944_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_implementation_contract_materialization_preflight/summary.json`
- follow-up manifest: `experiments/manifests/m2947-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-implementation-scaffold-local-search-synthesis.json`
- next: `m2947-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-implementation-scaffold-local-search-synthesis`

M2946 accepts that the audited M2944/M2945 contracts admit exactly one bounded implementation route. This is an admission decision only. It does not implement code, mutate checkpoints, execute an environment, train, validate, rank, promote, or claim implementation readiness, repair success, driver performance, paper evidence, high-fidelity readiness, full-driver completion, finite-window-vs-GRU evidence, or self-ID evidence.

The admitted route still needs a local-search synthesis before code, because the current branch has reached the non-evidence guard limit. M2947 must synthesize the M2940-M2946 chain and, only if it continues, register the scaffold as M2948.

## Admission Decision

Selected implementation route:

```text
bounded_actor_head_delta_implementation_scaffold_after_local_search_synthesis
```

This route admits one local-search synthesis milestone before the code-scaffold milestone. If that synthesis continues, the scaffold must add a reusable, testable residual actor-head delta wrapper with the following contract:

```text
input contract:
  actor observation shape remains 72.
  actor input remains the deployable parent actor observation only.
  no route/objective/constraint/diagnostic/success/progress/verdict labels become actor inputs.
  no hidden dynamics, oracle, future target, speed_ref, TTC, path error, heading error, curvature, stopping distance, or controller labels become actor inputs.

action contract:
  action shape remains 3.
  deployed action mapping remains steer / throttle / brake.
  zero residual reproduces the parent action path.
  residual output is bounded before action combination.
  combined action respects the existing action range contract.

implementation scope:
  add a reusable residual-head delta scaffold and unit tests.
  do not load, modify, save, rank, or promote checkpoints.
  do not run reset, step, rollout, replay, validation, training, PPO, dependency build, adapter probe, or external simulation.
```

## Preserved Contract Evidence

The admitted route must preserve the M2944 evidence:

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

The objective binding counts remain evaluator-side accounting only:

```text
persistent_offtrack_reduction: 24
collision_speed_anti_substitution: 10
success_context_retention: 9
positive_reference_preservation: 4
full_panel_accounting: 56
```

## M2947 Requirements

M2947 must synthesize the recent implementation-admission chain before code:

```text
synthesis artifact:
  answer evidence_summary, supported_claims, falsified_claims, failure_taxonomy_summary,
  public_gate_overfit_risk, implementation_scaffold_admission, and next_branch_decision.

decision:
  choose exactly one of continue to M2948 scaffold, artifact repair, pivot, or stop.
  do not bypass local_search_guard by raising the non-evidence limit.
  do not implement code, tests, checkpoint changes, execution, training, validation, ranking, or promotion.
```

If M2947 continues to M2948, the scaffold requirements are:

```text
code artifact:
  a small residual actor-head delta scaffold module under src/autodrift.
unit tests:
  shape contract 72 -> 3.
  zero-delta identity against a parent actor output.
  residual bound enforcement.
  no privileged/evaluator-label input keys in the scaffold contract.
  no checkpoint mutation or environment execution side effects.

documentation:
  milestone doc states that the scaffold is implementation infrastructure only.
  no implementation-readiness, validation, repair-success, performance, paper, high-fidelity, full-driver, finite-window-vs-GRU, or self-ID claim.
```

## Rejected Alternatives

```text
direct_training_or_validation:
  rejected because no implementation artifact exists yet and no checkpoint has been audited.

checkpoint_patch_or_promotion:
  rejected because M2947 may only synthesize and M2948 may only add scaffold code and tests if admitted.

full_policy_rewrite:
  rejected because M2944 admitted only a bounded residual actor-head delta contract.

evaluator_label_conditioned_actor:
  rejected because evaluator-side labels are not deployable observations.

implementation_readiness_claim:
  rejected because scaffold tests are not closed-loop validation or driver evidence.
```

## Claim Boundary

M2946 is admission design only. It proves only that one bounded scaffold route is allowed after local-search synthesis.

Rejected claims:

```text
implementation readiness or result
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
