# M1657 Paper-Route Selected Proposal Scope Sensitivity Result Audit

## Summary

M1657 audits the M1656 selected-proposal scope-sensitivity result before any
wider-scope repair design, checkpoint artifact, replay gate, PPO, or promotion.

Decision:

```text
scope_sensitivity_audit_admit_fusion_actor_repair_design
```

M1656 is a valid objective-sanity positive for one narrow claim: the M1653
actor_mean-only failure is not caused by a nondifferentiable selected-proposal
residual. The missing degree of freedom appears when the final fusion path is
made differentiable. The audit admits a design-only `fusion_actor` repair route,
not an implementation, checkpoint, replay gate, or promotion.

## Audited Evidence

Audited artifacts:

```text
runs/m1656_selected_proposal_scope_sensitivity/summary.json
runs/m1656_selected_proposal_scope_sensitivity/scope_summary.csv
runs/m1656_selected_proposal_scope_sensitivity/guardrail_summary.csv
docs/m1656-paper-route-selected-proposal-scope-sensitivity-implementation.md
```

Aggregate result:

```text
selected_candidate_count: 3
scope_count: 5
feature_mode_count: 2
scope_row_count: 30
frozen_feature_upstream_grad_zero: true
differentiable_feature_scope_measurable_count: 5
primary_alpha_0_2_wider_scope_nonzero_grad_count: 4
primary_alpha_0_2_wider_scope_reduction_count: 4
model_restored_after_probe_count: 15
passes_public_smoke_gates: true
null_result_classification: selected_proposal_scope_sensitivity_public_pass
```

Primary alpha `0.2` differentiable-feature result:

| Scope | Upstream Grad Norm | One-Step Reduction Ratio |
| --- | ---: | ---: |
| `fusion_actor` | 0.157123401761055 | 0.40519785496674926 |
| `context_fusion_actor` | 0.1630086898803711 | 0.4053135063761288 |
| `response_fusion_actor` | 0.1622813194990158 | 0.4005220459560401 |
| `full_policy_actor` | 0.16798587143421173 | 0.40066576536168946 |

`actor_mean` remained unable to reduce primary alpha `0.2`, matching M1653.

## Guardrail Audit

M1656 guardrails were clean:

```text
checkpoint_artifact_count: 0
diagnostic_rows_used_as_positive_count: 0
donor_plus_action_used_as_loss_target_count: 0
training_started_count: 0
ppo_used_count: 0
promoted_count: 0
private_holdout_used_count: 0
actor_input_contract_changed_count: 0
level3_self_id_claim_count: 0
```

The result is not contaminated by checkpoint writes, replay, PPO, training,
private holdout, actor-input changes, diagnostic-positive role leakage, or
level3 self-ID claims.

## Interpretation

Supported:

```text
the frozen-feature exact objective is structurally actor_mean-only;
differentiable-feature wider scopes expose upstream gradient;
the smallest wider scope, fusion_actor, is enough to produce a large one-step alpha 0.2 residual reduction;
adding context_encoder, response_encoder, or GRU scope is not yet justified by M1656 because the minimal wider scope already works similarly.
```

Unsupported:

```text
fusion_actor repair works as a full multi-step update;
wider-scope checkpoint artifacts are admissible;
closed-loop replay or behavior retention improved;
PPO-proposal repair works;
promotion is justified;
private-holdout or paper-level evidence exists;
level3 anticipatory self-identification is proven.
```

The audit chooses `fusion_actor` as the next design scope because it is the
smallest wider deterministic policy path tested and its primary alpha `0.2`
one-step reduction is effectively as strong as larger scopes.

## Route Decision

M1657 admits:

```text
m1658-paper-route-fusion-actor-proposal-repair-design
```

M1658 should design a no-checkpoint differentiable-feature repair probe over
`response_context_fusion.0.*` plus `actor_mean.*`. It must remain design-only
and keep checkpoint artifacts, replay gates, PPO, training, promotion, private
holdout, actor-input changes, paper-level claims, and level3 self-ID claims
blocked.
