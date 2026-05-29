# M1647 Paper-Route Contour-Aware Damped Projection Stress Test Result Audit

## Summary

M1647 audits the M1646 no-checkpoint damped projection stress-test pass before
any checkpoint artifact, PPO-proposal repair, or closed-loop route.

Decision:

```text
contour_aware_damped_projection_stress_audit_route_to_branch_synthesis
```

M1646 is a clean infrastructure pass. The damped projection rule is stable over
the fixed 3x3 controlled actor_mean perturbation grid. However, all evidence is
still fixed-tensor, public-row exact-objective plumbing. It should not be
upgraded directly to checkpoint artifact generation or PPO-proposal repair
without a branch-level synthesis.

This audit does not rerun stress tests, train, run PPO, run closed-loop
evaluation, write checkpoints, promote, use private holdout, change actor
inputs, or claim paper-level or level3 self-identification evidence.

## Audited Artifacts

```text
runs/m1646_contour_aware_damped_projection_stress_test/summary.json
runs/m1646_contour_aware_damped_projection_stress_test/candidate_summary.csv
runs/m1646_contour_aware_damped_projection_stress_test/aggregate_summary.csv
runs/m1646_contour_aware_damped_projection_stress_test/guardrail_summary.csv
docs/m1646-paper-route-contour-aware-damped-projection-stress-test-implementation.md
```

## Result Audit

M1646 passed:

```text
passes_public_smoke_gates: true
null_result_classification: damped_projection_stress_public_pass
```

Fixed-grid coverage:

```text
stress_candidate_count: 9
expected_stress_candidate_count: 9
perturb_scales: [1e-4, 3e-4, 1e-3]
perturb_seeds: [1645, 1646, 1647]
```

Aggregate exact-objective metrics:

```text
measurable_initial_residual_count: 9
residual_reduced_count: 9
candidate_public_pass_count: 9
accepted_backtracking_candidate_count: 9

min_positive_exact_residual_reduction_ratio:    0.7070986860856349
median_positive_exact_residual_reduction_ratio: 0.7420973915926545
max_positive_exact_residual_reduction_ratio:    0.8632753818236488
```

Guardrails:

```text
max_guardrail_violation_count: 0
checkpoint_artifact_count: 0
base_interpolation_used_for_repair_count: 0
diagnostic_rows_used_as_positive_count: 0
donor_plus_action_used_as_loss_target_count: 0
training_started_count: 0
ppo_used_count: 0
promoted_count: 0
private_holdout_used_count: 0
actor_input_contract_changed_count: 0
level3_self_id_claim_count: 0
```

## Supported Claims

M1647 supports:

```text
the damped projection rule is stable across the pre-registered small actor_mean perturbation grid;
the exact objective can restore controlled policy-output drift without writing checkpoints;
no-base-reset, diagnostics-zero-weight, donor-plus exclusion, and no-checkpoint guardrails are enforced;
the branch has enough infrastructure evidence for synthesis.
```

## Unsupported Claims

M1647 keeps unsupported:

```text
checkpoint artifact generation;
PPO-proposal repair;
closed-loop replay improvement;
behavior retention;
promotion;
private-holdout evidence;
paper-level evidence;
level3 anticipatory self-identification.
```

## Why Synthesis Before Next Implementation

The M1640-M1646 sequence now contains:

```text
one negative Adam projection result;
one audit classifying optimizer-step instability;
one damped projection design;
one local damped projection pass;
one audit preserving the local claim boundary;
one fixed-grid stress design;
one fixed-grid stress pass.
```

That is enough local projection tooling. Another implementation on the same
public tensor package would increase public-row overfit risk more than it would
advance the paper route.

The next decision should be branch-level:

```text
Should this exact-objective projection tool move into a PPO-proposal repair branch?
Should it first create a checkpoint-artifact design?
Should the branch stop because fixed public tensors are too narrow?
```

Those questions belong in synthesis, not another immediate implementation.

## Next Route

Route to branch synthesis:

```text
m1648-paper-route-contour-aware-damped-projection-branch-synthesis
```

M1648 should answer:

```text
evidence_summary
supported_claims
falsified_claims
failure_taxonomy_summary
public_gate_overfit_risk
next_branch_decision
```

M1647 does not admit checkpoint artifacts, PPO-proposal repair, closed-loop
evaluation, promotion, private holdout, actor-input changes, or level3 self-ID
claims.
