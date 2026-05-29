# M1656 Paper-Route Selected Proposal Scope Sensitivity Implementation

## Summary

M1656 implements and runs the no-checkpoint two-mode selected-proposal
scope-sensitivity preflight designed in M1655.

Decision:

```text
selected_proposal_scope_sensitivity_public_pass_route_to_audit
```

The result is positive for the narrow question tested here: the frozen-feature
sanity check confirms that upstream gradients are zero in the old M1640-M1653
feature-frozen path, while differentiable-feature wider scopes expose nonzero
upstream gradients and one-step exact-residual reductions on the primary alpha
`0.2` proposal where actor_mean-only repair failed.

This is still not a repaired checkpoint, not PPO, not closed-loop replay, not a
promotion result, not private-holdout evidence, and not level3
self-identification evidence.

## Implementation

Added:

```text
src/autodrift/selected_proposal_scope_sensitivity.py
tests/test_selected_proposal_scope_sensitivity.py
```

The implementation compares:

```text
feature modes:
  frozen_feature
  differentiable_feature

scopes:
  actor_mean
  fusion_actor
  context_fusion_actor
  response_fusion_actor
  full_policy_actor
```

It excludes:

```text
critic.*
response_prediction_head.*
log_std
```

Each one-step candidate is temporary and in-memory only. The probe restores
model state before writing metrics.

## Validation

Focused test:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m pytest -q tests/test_selected_proposal_scope_sensitivity.py
```

Result:

```text
3 passed in 2.06s
```

Official M1656 run:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.selected_proposal_scope_sensitivity \
  --base-checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --candidate-summary runs/m1650_proposal_source_preflight/candidate_summary.csv \
  --materialization-run-dir runs/m1630_contour_aware_full_target_materialization \
  --run-dir runs/m1656_selected_proposal_scope_sensitivity \
  --selected-alphas 0.2,0.4,1.0
```

Artifacts:

```text
runs/m1656_selected_proposal_scope_sensitivity/summary.json
runs/m1656_selected_proposal_scope_sensitivity/scope_summary.csv
runs/m1656_selected_proposal_scope_sensitivity/aggregate_summary.csv
runs/m1656_selected_proposal_scope_sensitivity/guardrail_summary.csv
```

## Aggregate Result

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

| Scope | Grad Norm | Upstream Grad Norm | One-Step Reduced | Reduction Ratio | Factor |
| --- | ---: | ---: | --- | ---: | ---: |
| `actor_mean` | 0.8779878616333008 | 0.0 | false | 0.0 |  |
| `fusion_actor` | 0.8919363021850586 | 0.157123401761055 | true | 0.40519785496674926 | 0.125 |
| `context_fusion_actor` | 0.8929919004440308 | 0.1630086898803711 | true | 0.4053135063761288 | 0.125 |
| `response_fusion_actor` | 0.8928593993186951 | 0.1622813194990158 | true | 0.4005220459560401 | 0.125 |
| `full_policy_actor` | 0.8939138650894165 | 0.16798587143421173 | true | 0.40066576536168946 | 0.125 |

Interpretation:

```text
actor_mean-only still cannot reduce the primary alpha 0.2 residual.
The failure is not because the selected proposal residual is inherently non-differentiable.
The missing degree of freedom appears in the fusion/feature path once features are recomputed differentiably.
```

## Guardrails

Guardrail counts:

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

No `.pt` or `.pth` files exist under the M1656 run directory.

## Supported Claims

M1656 supports:

```text
the M1640-M1653 frozen-feature exact objective is structurally actor_mean-only;
differentiable-feature wider deterministic actor scopes expose upstream gradient on the selected proposals;
fusion_actor and wider scopes can reduce the primary alpha 0.2 exact residual in a temporary one-step sensitivity probe;
the scope-sensitivity tooling writes metrics without checkpoint artifacts or role contamination.
```

## Unsupported Claims

M1656 does not support:

```text
wider-scope repair works as a full update;
checkpoint artifact generation;
closed-loop replay improvement;
behavior retention;
PPO-proposal repair;
promotion;
private-holdout evidence;
paper-level evidence;
level3 anticipatory self-identification.
```

## Next Route

Route to result audit:

```text
m1657-paper-route-selected-proposal-scope-sensitivity-result-audit
```

M1657 should audit this positive scope-sensitivity result before any wider-scope
repair design, checkpoint artifact, replay gate, PPO, or promotion.
