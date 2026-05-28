# M1286 Paper-Route Four-Wheel Source Intervention Materialization Synthesis

## Summary

M1286 synthesizes the `paper_route_four_wheel_source_intervention_materialization`
branch from M1276 through M1285.

Synthesis decision:

```text
promote_to_next_branch
```

Decision:

```text
four_wheel_source_intervention_materialization_synthesis_promote_to_source_history_objective_only_update
```

The branch should close as a materialization/evaluator branch and promote to a
new branch:

```text
paper_route_source_history_objective_only_update
```

Rationale:

```text
M1276-M1285 created clean preferred/rejected source intervention artifacts,
branch-specific response histories, a policy-side correct-history versus
wrong-history gate, and an exact no-update source-history objective evaluator.
The current public-gate checkpoint does not yet use the new histories in the
desired direction, but the residual is now measurable and finite. The next
question is whether an objective-only update can reduce this residual without
breaking existing public proof gates.
```

No training, PPO, checkpoint promotion, private holdout, actor-input expansion,
accepted-threshold relaxation, high-fidelity validation claim, paper-level
claim, or self-identification claim occurs in M1286.

## Evidence Summary

M1276 designed the source-intervention materialization schema:

```text
primary subset: near_boundary OR high_regret
source pairs: 38
expected branch-conditioned intervention rows: 76
secondary family-balanced rows: 126
```

M1277 materialized the artifacts:

```text
intervention_rows: 202
observation_rows: 202
action_sequence_rows: 29088
observation_dim: 72
observation_all_finite: true
preferred_success_fail_count: 0
preferred_margin_negative_count: 0
margin_gap_below_threshold_count: 0
```

M1278 audited the blocker:

```text
M1277 artifacts are clean, but direct policy training is blocked because the
same current source observation can require different preferred actions under
hidden branch A or B.
```

M1279 designed branch-specific response histories, and M1280 materialized them:

```text
history_prefix_rows: 152
history_frame_rows: 3648
history_intervention_rows: 152
wrong_history_pair_rows: 152
wrong_history_valid_count: 152
```

M1281 audited M1280:

```text
unique source pairs: 38
unique interventions: 76
wrong-history swaps: 152/152 same-pair opposite-condition
response_l2_min: 0.0157835288
response_l2_mean: 0.2109745544
final_yaw_rate_diff_ge_0_01_count: 152/152
```

M1282 designed the policy-side gate:

```text
canonical 72-frame projection;
cmd_* fields are prefix action metadata, not actor inputs;
correct-history versus wrong-history hidden states queried at the same current
intervention observation.
```

M1283 implemented and ran the gate:

```text
row_count: 152
finite_row_count: 152
projection_valid_count: 152
wrong_history_valid_count: 152
result_class: action_level_history_signal_weak
both_directional_fraction: 0.0
preferred_hidden_margin_positive_fraction: 0.4868421053
history_action_l2_mean: 0.0991899077
```

M1284 designed the exact source-history objective:

```text
L_correct = softplus(logp_cr - logp_cp + 0.05)
L_wrong   = softplus(logp_wp - logp_wr + 0.05)
L_total   = L_correct + L_wrong
```

M1285 implemented and ran the no-update evaluator:

```text
result_class: source_history_objective_evaluator_pass
row_count: 152
finite_row_count: 152
exact_objective_finite: true
checkpoint_weights_mutated: false
combined_loss_mean: 18.6105005708
```

## Supported Claims

Supported:

```text
The M1273 source corpus can be materialized into clean preferred/rejected
intervention artifacts without leaking fault labels into 72-value observations.
```

Supported:

```text
The source intervention artifacts contain useful outcome contrast:
preferred actions succeed with nonnegative margins and rejected actions include
both success-drop and lower-margin counterfactuals.
```

Supported:

```text
Branch-specific command-response histories can be generated for the near/high
source subset, and same-pair wrong-history swaps are well defined.
```

Supported:

```text
The M1280 histories are actor-contract compatible after canonical projection:
response fields can be mapped to indices 0..11, while metadata and cmd_* fields
remain outside actor inputs.
```

Supported:

```text
The current public-gate checkpoint is sensitive to the generated histories at
the action-mean level: M1283 history_action_l2_mean is 0.0991899077.
```

Supported:

```text
The exact source-history preference residual is finite on the full 152-row
corpus and can be used as a future objective-only optimization target.
```

## Falsified Claims

Falsified:

```text
M1277 current-frame intervention rows can be used directly for policy training.
They are label-contradictory without response history.
```

Falsified:

```text
The current public-gate checkpoint already uses M1280 histories in the desired
source-branch direction. M1283 both_directional_fraction is 0.0.
```

Falsified:

```text
Nonzero action movement from source histories is enough for PPO admission.
M1283 shows movement, but the direction is wrong/weak.
```

Falsified:

```text
A source-history gate result by itself proves self-identification or
closed-loop driver behavior. M1283 and M1285 are action-level/evaluator
artifacts only.
```

Not yet proven:

```text
An objective-only update can reduce the exact source-history residual.
```

Not yet proven:

```text
Reducing the source-history objective can preserve old public proof gates.
```

Not yet proven:

```text
The source-history objective improves closed-loop obstacle avoidance.
```

Not yet proven:

```text
The compact four-wheel source model is high-fidelity or real-vehicle validated.
```

## Failure Taxonomy Summary

Resolved blocker:

```text
contract_violation risk:
  M1281/M1282 identified that cmd_* and fault metadata must not be actor inputs.
  M1283 implemented canonical projection and validated finite 72-value frames.
```

Resolved blocker:

```text
lineage_invalid risk:
  Direct M1277 policy use was blocked, and the branch inserted M1279-M1281
  response-history materialization/audit before policy-side use.
```

Active failure:

```text
objective_overfit / source_history_residual:
  M1283 shows the current checkpoint is not directionally aligned with the
  source-history preferred/rejected relation. M1285 quantifies the exact
  residual with combined_loss_mean = 18.6105005708.
```

Active risk:

```text
proof_washout:
  Any future objective-only update may reduce M1285 loss while damaging old
  public proof gates. The next branch must start with objective-only design and
  strict retention planning, not PPO.
```

Not observed:

```text
training_instability:
  No training occurred in this branch.
```

Not observed:

```text
private_holdout_contamination:
  No private holdout was used.
```

## Public Gate Overfit Risk

Risk level:

```text
moderate to high for the next branch
```

Reasons:

```text
The M1280/M1277/M1285 source-history corpus has only 152 policy-side rows.
It is public and has now been used for multiple designs and exact evaluators.
An optimizer could easily overfit this corpus while failing old replay surfaces
or fresh source-history variants.
```

Mitigations for the next branch:

```text
start with objective-only update design, not PPO;
evaluate exact M1285 loss before any public replay gates;
use small trusted trainable scopes first;
include trust-region and checkpoint-delta diagnostics;
run old public proof gates only after exact loss improves;
do not use private holdout until a candidate survives public proof retention;
refresh a source-history surface before paper-level claims.
```

## Next Branch Decision

Promote to a new branch:

```text
paper_route_source_history_objective_only_update
```

First next milestone:

```text
m1287-paper-route-source-history-objective-only-update-design
```

M1287 should design, but not run, an objective-only update around the M1285
exact residual.

Required constraints:

```text
no PPO;
no promotion;
no private holdout;
no actor-input expansion;
exact M1285 loss must be the first gate;
public proof-retention gates come after exact-loss improvement;
branch must include a future source-history refresh before any paper-level
claim.
```

Possible trainable scopes, in order:

```text
actor_mean_only;
response_context_fusion + actor_mean;
response_encoder + GRU + fusion + actor_mean.
```

The next branch should decide whether a small exact objective-only update can
reduce source-history residual without damaging existing public proof surfaces.
PPO remains blocked until that is shown.
