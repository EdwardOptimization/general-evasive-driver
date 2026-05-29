# M1660 Paper-Route Fusion Actor Proposal Repair Implementation

## Summary

M1660 implements and runs the no-checkpoint differentiable-feature
`fusion_actor` selected-proposal repair probe admitted by M1659 synthesis.

Decision:

```text
fusion_actor_proposal_repair_public_pass_route_to_audit
```

The implementation passes the pre-registered public objective-sanity gate: all
three selected proposal candidates pass, including primary alpha `0.2`. No
checkpoint artifacts were written, model state was restored after each temporary
in-memory repair, and role/contract guardrails stayed clean.

This remains fixed-public-tensor objective-sanity evidence. It is not a
checkpoint artifact, closed-loop replay, behavior-retention, PPO, promotion,
private-holdout, paper-level, or level3 self-identification result.

## Implementation

Added:

```text
src/autodrift/fusion_actor_proposal_repair.py
tests/test_fusion_actor_proposal_repair.py
```

Repair scope:

```text
response_context_fusion.0.weight
response_context_fusion.0.bias
actor_mean.weight
actor_mean.bias
```

Feature mode:

```text
differentiable_feature
```

## Validation

Focused test:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m pytest -q tests/test_fusion_actor_proposal_repair.py
```

Result:

```text
3 passed in 0.93s
```

Official M1660 run:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.fusion_actor_proposal_repair \
  --base-checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --candidate-summary runs/m1650_proposal_source_preflight/candidate_summary.csv \
  --materialization-run-dir runs/m1630_contour_aware_full_target_materialization \
  --run-dir runs/m1660_fusion_actor_proposal_repair \
  --selected-alphas 0.2,0.4,1.0
```

Artifacts:

```text
runs/m1660_fusion_actor_proposal_repair/summary.json
runs/m1660_fusion_actor_proposal_repair/candidate_summary.csv
runs/m1660_fusion_actor_proposal_repair/aggregate_summary.csv
runs/m1660_fusion_actor_proposal_repair/guardrail_summary.csv
runs/m1660_fusion_actor_proposal_repair/candidates/
```

## Aggregate Result

```text
selected_candidate_count: 3
measurable_initial_residual_count: 3
candidate_public_pass_count: 3
primary_alpha_0_2_pass: true
model_restored_after_probe_count: 3
excluded_parameter_delta_violation_count: 0
checkpoint_artifact_count: 0
passes_public_smoke_gates: true
null_result_classification: fusion_actor_proposal_repair_public_pass
```

Candidate result:

| Alpha | Initial Exact | Repaired Exact | Reduction Ratio | Accepted Steps | Candidate Gate |
| --- | ---: | ---: | ---: | ---: | --- |
| 0.2 | 0.0012401377316564322 | 0.0007376365829259157 | 0.40519785496674926 | 1 | true |
| 0.4 | 0.010803105309605598 | 0.006825495511293411 | 0.3681913379827455 | 1 | true |
| 1.0 | 0.08403468132019043 | 0.01239560917019844 | 0.8524941253365563 | 2 | true |

## Guardrails

Guardrail counts:

```text
checkpoint_artifact_count: 0
excluded_parameter_delta_violation_count: 0
diagnostic_rows_used_as_positive_count: 0
donor_plus_action_used_as_loss_target_count: 0
training_started_count: 0
ppo_used_count: 0
promoted_count: 0
private_holdout_used_count: 0
actor_input_contract_changed_count: 0
level3_self_id_claim_count: 0
```

No `.pt` or `.pth` files exist under the M1660 run directory.

## Supported Claims

M1660 supports:

```text
differentiable-feature fusion_actor repair can reduce selected same-line proposal exact residuals;
primary alpha 0.2 passes the pre-registered 25% reduction gate;
all selected alpha 0.2, 0.4, and 1.0 candidates pass as no-checkpoint metric artifacts;
the implementation keeps checkpoint, excluded-parameter, diagnostics, donor-plus, training, PPO, promotion, private-holdout, actor-input, and level3 guardrails clean.
```

## Unsupported Claims

M1660 does not support:

```text
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
m1661-paper-route-fusion-actor-proposal-repair-result-audit
```

M1661 must audit this positive objective-sanity result before any checkpoint
artifact design, replay gate, PPO route, or promotion.
