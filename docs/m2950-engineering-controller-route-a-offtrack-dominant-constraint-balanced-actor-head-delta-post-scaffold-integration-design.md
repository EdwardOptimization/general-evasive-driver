# M2950 Engineering Controller Route A Offtrack-Dominant Constraint-Balanced Actor-Head Delta Post-Scaffold Integration Design

## Summary

- status: completed
- decision: `admit_m2951_post_scaffold_integration_contract_materialization_preflight`
- manifest: `experiments/manifests/m2950-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-post-scaffold-integration-design.json`
- parent audit: `docs/m2949-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-implementation-scaffold-result-audit.md`
- scaffold: `src/autodrift/constraint_balanced_actor_head_delta_scaffold.py`
- follow-up manifest: `experiments/manifests/m2951-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-post-scaffold-integration-contract-materialization-preflight.json`

M2950 selects exactly one post-scaffold route: a no-execution integration-contract materialization preflight. It does not implement the materializer, run the materializer, load or mutate checkpoints, execute an environment, train, validate, rank, promote, or claim implementation readiness, repair success, driver performance, paper evidence, high-fidelity readiness, full-driver completion, finite-window-vs-GRU evidence, or self-ID evidence.

## Selected Route

```text
post_scaffold_integration_contract_materialization_preflight
```

The route is admitted because M2949 accepts M2948 as claim-safe infrastructure, but the scaffold still needs machine-checkable integration contracts before any residual-head candidate can be built or executed.

## Integration Contract

M2951 must materialize rows for these surfaces:

```text
integration_surface:
  parent actor callable remains the source of the base action.
  residual head receives only the same deployable 72-value actor observation.
  scaffold combines parent action plus bounded residual delta.

actor_binding:
  actor observation shape 72.
  action shape 3.
  channel order steer / throttle / brake.
  distribution parent output is interpreted as tanh(mean), matching existing deployed action helpers.

residual_head_initialization:
  zero residual path must reproduce the parent actor output.
  any trainable residual head must support zero-initialized final output.
  no full-policy rewrite or parent-trunk mutation is admitted by this design.

residual_bound:
  residual delta is bounded before action combination.
  combined action is clamped to configured action range.
  bound values remain explicit materialized contract fields before later implementation.

input_guard:
  forbidden evaluator and privileged actor input keys remain blocked.
  route/objective/constraint/diagnostic/success/progress/verdict labels remain actor-invisible.

side_effect_guard:
  no checkpoint load/modify/save/rank/promote.
  no environment reset/step/rollout/replay/validation/training/PPO/dependency build/adapter probe/external simulation.

claim_boundary:
  scaffold and integration contracts are infrastructure only.
  no implementation-readiness, repair-success, performance, paper, high-fidelity, full-driver, finite-window-vs-GRU, or self-ID claim.
```

## M2951 Requirements

M2951 may add a materialization preflight implementation and tests that write machine-checkable rows. The minimum row groups are:

```text
integration_surface_rows
actor_binding_rows
residual_head_initialization_rows
residual_bound_rows
input_guard_rows
side_effect_guard_rows
claim_boundary_rows
gate_matrix
summary
```

M2951 must route to a result audit before any candidate execution or interpretation.

## Rejected Alternatives

```text
direct_candidate_execution:
  rejected because no integration contracts have been materialized or audited.

checkpoint_patch_or_training:
  rejected because M2950 is design-only and M2951 is limited to materialization preflight.

parent_policy_rewrite:
  rejected because the accepted route is a bounded residual actor-head delta scaffold.

evaluator_label_conditioning:
  rejected because deployable actor input remains the 72-value observation only.

implementation_readiness_claim:
  rejected because scaffold tests and integration design are not closed-loop validation.
```

## Claim Boundary

M2950 proves only that one bounded integration-contract materialization route is allowed next.
