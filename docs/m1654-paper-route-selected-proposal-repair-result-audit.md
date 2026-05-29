# M1654 Paper-Route Selected Proposal Repair Result Audit

## Summary

M1654 audits the M1653 selected-proposal repair result before any rerun,
wider-scope repair, checkpoint artifact, replay gate, PPO, or promotion.

Decision:

```text
selected_proposal_repair_audit_admit_scope_sensitivity_design
```

M1653 is a clean negative for the pre-registered actor_mean-only repair rule:
the implementation and guardrails worked, but the primary alpha `0.2` proposal
did not improve. Alpha `1.0` showed a small measurable reduction, but it was
below the candidate gate and cannot be treated as a pass.

## Audited Evidence

Audited artifacts:

```text
runs/m1653_selected_proposal_repair/summary.json
runs/m1653_selected_proposal_repair/candidate_summary.csv
runs/m1653_selected_proposal_repair/aggregate_summary.csv
runs/m1653_selected_proposal_repair/guardrail_summary.csv
docs/m1653-paper-route-selected-proposal-repair-implementation.md
```

Aggregate result:

```text
selected_candidate_count: 3
measurable_initial_residual_count: 3
residual_reduced_count: 1
candidate_public_pass_count: 0
primary_alpha_0_2_pass: false
passes_public_smoke_gates: false
null_result_classification: selected_proposal_repair_scope_insufficient
```

Candidate result:

| Alpha | Initial Exact | Repaired Exact | Reduction Ratio | Accepted Steps | Classification |
| --- | ---: | ---: | ---: | ---: | --- |
| 0.2 | 0.0012401377316564322 | 0.0012401377316564322 | 0.0 | 0 | `residual_not_reduced` |
| 0.4 | 0.010803105309605598 | 0.010803105309605598 | 0.0 | 0 | `residual_not_reduced` |
| 1.0 | 0.08403468132019043 | 0.07793601602315903 | 0.07257319479554114 | 1 | `reduction_ratio_below_threshold` |

## Guardrail Audit

M1653 did not violate the process guardrails:

```text
checkpoint_artifact_count: 0
base_interpolation_used_for_repair_count: 0
non_actor_mean_parameter_changed_count: 0
diagnostic_rows_used_as_positive_count: 0
donor_plus_action_used_as_loss_target_count: 0
training_started_count: 0
ppo_used_count: 0
promoted_count: 0
private_holdout_used_count: 0
actor_input_contract_changed_count: 0
level3_self_id_claim_count: 0
```

The result is therefore not a plumbing failure, checkpoint mutation artifact,
role-contamination artifact, or actor-input-contract violation.

## Failure Classification

Failure taxonomy:

```text
training_instability
```

In this milestone, the taxonomy label means projection/scope insufficiency:
the exact objective was connected and measurable, but the actor_mean-only
damped projection rule could not improve the primary selected proposal and did
not pass any candidate gate. No environment training or PPO ran.

## Interpretation

Supported:

```text
M1653 cleanly tests the actor_mean-only selected-proposal repair rule.
M1362 same-line proposal residuals are measurable on the M1630 exact tensors.
The current rule is insufficient for the primary alpha 0.2 selected proposal.
The alpha 1.0 partial reduction shows the objective has some local signal, but not enough for the pre-registered gate.
```

Unsupported:

```text
selected-proposal repair works;
PPO-proposal repair works;
checkpoint artifact generation is admitted;
closed-loop replay or behavior retention improved;
the proposal-repair branch should promote;
private-holdout or paper-level evidence exists;
level3 anticipatory self-identification is proven.
```

The correct route is not to tune the M1653 step factors after seeing the result
and not to jump directly to checkpoint artifacts. The clean next question is
whether the failure is caused by the narrow trainable scope, the proposal
geometry, or the exact-objective active set.

## Route Decision

M1654 admits a design-only scope-sensitivity milestone:

```text
m1655-paper-route-selected-proposal-scope-sensitivity-design
```

M1655 should design a no-checkpoint, no-update preflight that inventories
candidate trainable scopes and their exact-objective gradient/reduction signal
on the same selected proposals. It must keep checkpoint artifacts, replay gates,
PPO, training, promotion, private holdout, actor-input changes, and level3
self-ID claims blocked.
